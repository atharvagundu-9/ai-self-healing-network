from __future__ import annotations

import asyncio
import json
import logging
import time
from collections import deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.api.schemas import FaultRequest, HealingRequest
from backend.config import MODEL_DIR
from backend.database import db
from backend.healing.healing_engine import HealingEngine, severity_for
from backend.healing.root_cause import analyze
from backend.ml.anomaly_detector import AnomalyDetector
from backend.ml.failure_predictor import FailurePredictor
from backend.network.simulator import NetworkSimulator


# Use Uvicorn's configured logger so demo events are always visible in the
# backend terminal without requiring a separate logging configuration file.
logger = logging.getLogger("uvicorn.error")


def metric_health(row: dict) -> float:
    latency_penalty = min(22, max(0, row["latency_ms"] - 25) * 0.14)
    loss_penalty = min(28, row["packet_loss_percent"] * 2.2)
    bandwidth_penalty = min(14, max(0, row["bandwidth_utilization"] - 70) * 0.45)
    cpu_penalty = min(12, max(0, row["cpu_usage_percent"] - 70) * 0.4)
    availability_penalty = 35 if row["device_status"] == "offline" else 0
    return max(0.0, 100 - latency_penalty - loss_penalty - bandwidth_penalty - cpu_penalty - availability_penalty)


class SocketHub:
    def __init__(self) -> None:
        self.clients: set[WebSocket] = set()

    async def connect(self, socket: WebSocket) -> None:
        await socket.accept()
        self.clients.add(socket)

    def disconnect(self, socket: WebSocket) -> None:
        self.clients.discard(socket)

    async def broadcast(self, payload: dict) -> None:
        stale = []
        for client in self.clients:
            try:
                await client.send_json(payload)
            except Exception:
                stale.append(client)
        for client in stale:
            self.disconnect(client)


@dataclass
class Runtime:
    simulator: NetworkSimulator = field(default_factory=NetworkSimulator)
    healing: HealingEngine = field(default_factory=HealingEngine)
    sockets: SocketHub = field(default_factory=SocketHub)
    telemetry: list[dict] = field(default_factory=list)
    latest_prediction: dict | None = None
    latest_diagnosis: dict | None = None
    latest_risk: dict | None = None
    active_incident: dict | None = None
    successful_recoveries: int = 0
    backend_logs: deque = field(default_factory=lambda: deque(maxlen=120))
    task: asyncio.Task | None = None

    def console(self, level: str, category: str, message: str) -> None:
        """Keep a bounded copy of backend activity for the live dashboard console."""
        self.backend_logs.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "category": category,
            "message": message,
        })

    def initialize(self) -> None:
        topology = self.simulator.topology()
        db.init_db(topology["devices"])
        self.anomaly = AnomalyDetector()
        self.predictor = FailurePredictor()
        logger.info("[AEGIS][STARTUP] Monitoring engine online | devices=%d | interval=1s", len(topology["devices"]))
        self.console("INFO", "STARTUP", f"Monitoring engine online | devices={len(topology['devices'])} | interval=1s")

    def network_health(self, rows: list[dict] | None = None) -> float:
        rows = rows or self.telemetry
        if not rows:
            return 100.0
        base = sum(metric_health(row) for row in rows) / len(rows)
        incident_penalty = 5 if self.active_incident else 0
        return round(max(0, base - incident_penalty), 1)

    def status(self) -> dict:
        offline = sum(1 for row in self.telemetry if row["device_status"] == "offline")
        return {
            "network_health": self.network_health(),
            "active_devices": max(0, 8 - offline),
            "total_devices": 8,
            "active_alerts": 1 if self.active_incident else 0,
            "predicted_failures": 1 if self.active_incident and self.latest_prediction and self.latest_prediction["predicted_failure"] != "normal" else 0,
            "successful_recoveries": self.successful_recoveries,
            "mode": "SIMULATION",
            "phase": self.active_incident["phase"] if self.active_incident else "monitoring",
        }

    async def loop(self) -> None:
        while True:
            try:
                rows = self.simulator.snapshot()
                self.telemetry = rows
                db.insert_telemetry(rows)
                await self.process_fault(rows)
                await self.sockets.broadcast(self.payload())
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                db.add_event("engine_error", f"Monitoring loop recovered from error: {exc}", "ERROR")
                logger.exception("[AEGIS][ENGINE] Monitoring loop recovered from an error")
                self.console("ERROR", "ENGINE", f"Monitoring loop recovered from error: {exc}")
            await asyncio.sleep(1)

    async def process_fault(self, rows: list[dict]) -> None:
        fault = self.simulator.fault
        target_id = fault["device_id"] if fault else (self.active_incident["device_id"] if self.active_incident else None)
        target = next((row for row in rows if target_id and row["device_id"] == target_id), None)
        if not target:
            return
        if fault:
            telemetry_message = (
                f"stage={fault['progress']}/10 | latency={target['latency_ms']:.1f}ms | "
                f"loss={target['packet_loss_percent']:.1f}% | bandwidth={target['bandwidth_utilization']:.1f}% | "
                f"throughput={target['throughput_mbps']:.1f}Mbps | cpu={target['cpu_usage_percent']:.1f}% | "
                f"memory={target['memory_usage_percent']:.1f}% | status={target['device_status'].upper()}"
            )
            logger.info(
                "[AEGIS][TELEMETRY][%s][%s] stage=%d/10 | latency=%.1fms | loss=%.1f%% | bandwidth=%.1f%% | throughput=%.1fMbps | cpu=%.1f%% | memory=%.1f%% | status=%s",
                fault["type"].upper(), target["device_id"].upper(), fault["progress"],
                target["latency_ms"], target["packet_loss_percent"], target["bandwidth_utilization"],
                target["throughput_mbps"], target["cpu_usage_percent"], target["memory_usage_percent"],
                target["device_status"].upper(),
            )
            self.console("INFO", f"TELEMETRY/{fault['type'].upper()}/{target['device_id'].upper()}", telemetry_message)
        if self.active_incident:
            await self.verify_or_rollback(target)
            return
        anomaly = self.anomaly.predict(target)
        prediction = self.predictor.predict(target)
        risk = self.predictor.failure_risk(target)
        prediction["device_id"] = target["device_id"]
        prediction["anomaly"] = anomaly
        self.latest_prediction = prediction
        self.latest_risk = risk

        if not anomaly["is_anomaly"] or prediction["predicted_failure"] == "normal":
            return

        severity = severity_for(target, prediction["confidence"])
        diagnosis = analyze(target, prediction["predicted_failure"], prediction["confidence"])
        self.latest_diagnosis = diagnosis
        if severity == "LOW":
            message = "Anomaly is below the automatic-action threshold; continuing observation as metrics develop"
            logger.info("[AEGIS][SAFETY][%s] %s", target["device_id"].upper(), message)
            self.console("INFO", f"SAFETY/{target['device_id'].upper()}", message)
            return
        db.add_prediction(target["device_id"], prediction)
        before_metrics = {**target, "health_score": self.network_health(rows)}
        incident_id = db.create_incident(target["device_id"], prediction["predicted_failure"], severity, diagnosis, before_metrics)
        db.add_event("anomaly_detected", f"Anomaly detected on {target['device_id']}", severity, target["device_id"], incident_id)
        db.add_event("failure_predicted", f"{prediction['predicted_failure'].replace('_', ' ').title()} predicted ({prediction['confidence']:.0%})", severity, target["device_id"], incident_id)
        db.add_event("root_cause", diagnosis["probable_cause"], severity, target["device_id"], incident_id)
        logger.warning(
            "[AEGIS][DETECTION][%s] anomaly=true | score=%.2f | severity=%s",
            target["device_id"].upper(), anomaly["anomaly_score"], severity,
        )
        self.console("WARNING", f"DETECTION/{target['device_id'].upper()}", f"anomaly=true | score={anomaly['anomaly_score']:.2f} | severity={severity}")
        logger.warning(
            "[AEGIS][PREDICTION][%s] failure=%s | confidence=%.1f%%",
            target["device_id"].upper(), prediction["predicted_failure"].upper(), prediction["confidence"] * 100,
        )
        self.console("WARNING", f"PREDICTION/{target['device_id'].upper()}", f"failure={prediction['predicted_failure'].upper()} | confidence={prediction['confidence'] * 100:.1f}%")
        logger.warning(
            "[AEGIS][ROOT-CAUSE][%s] %s | evidence=%s",
            target["device_id"].upper(), diagnosis["probable_cause"], diagnosis["relevant_metrics"],
        )
        self.console("WARNING", f"ROOT-CAUSE/{target['device_id'].upper()}", f"{diagnosis['probable_cause']} | evidence={diagnosis['relevant_metrics']}")
        self.active_incident = {
            "id": incident_id, "device_id": target["device_id"], "failure_type": prediction["predicted_failure"],
            "severity": severity, "before": before_metrics, "before_health": self.network_health(rows),
            "started": time.monotonic(), "phase": "diagnosis", "action": None,
        }
        await self.execute_healing(target["device_id"], prediction["predicted_failure"], severity, incident_id)

    async def execute_healing(self, device_id: str, failure_type: str, severity: str, incident_id: int | None) -> dict:
        decision = self.healing.select(failure_type, device_id, severity)
        if not decision["approved"]:
            db.add_event("action_blocked", decision["reason"], "WARNING", device_id, incident_id)
            logger.warning("[AEGIS][SAFETY][%s] action blocked | %s", device_id.upper(), decision["reason"])
            self.console("WARNING", f"SAFETY/{device_id.upper()}", f"action blocked | {decision['reason']}")
            return decision
        action = decision["action"]
        self.healing.mark_executed(device_id, action)
        self.simulator.apply_healing(action, device_id)
        db.add_action(incident_id, device_id, action, "executing", decision["label"])
        db.add_event("healing_started", decision["label"], "INFO", device_id, incident_id)
        logger.info(
            "[AEGIS][HEALING][%s] action=%s | description=%s | simulated=true",
            device_id.upper(), action.upper(), decision["label"],
        )
        self.console("INFO", f"HEALING/{device_id.upper()}", f"action={action.upper()} | {decision['label']} | simulated=true")
        if self.active_incident and self.active_incident["id"] == incident_id:
            self.active_incident["phase"] = "healing"
            self.active_incident["action"] = decision
        return decision

    async def verify_or_rollback(self, target: dict) -> None:
        incident = self.active_incident
        if not incident or incident["phase"] != "healing":
            return
        elapsed = time.monotonic() - incident["started"]
        recovered = target["device_status"] == "healing" and elapsed >= 4 and metric_health(target) >= 78
        simulator_done = self.simulator.healing is None
        if recovered or (simulator_done and metric_health(target) >= 78):
            # Verification measures recovered telemetry without the temporary
            # active-incident UI penalty that is removed immediately afterward.
            after_health = round(sum(metric_health(row) for row in self.telemetry) / len(self.telemetry), 1)
            after = {**target, "device_status": "healthy", "health_score": after_health}
            recovery_time = round(elapsed, 2)
            db.update_incident(incident["id"], "recovered", after, recovery_time)
            db.add_action(incident["id"], target["device_id"], incident["action"]["action"], "verified", "Post-action metrics returned to a healthy range.")
            db.add_event("recovery_verified", f"Recovery verified in {recovery_time:.1f}s", "SUCCESS", target["device_id"], incident["id"])
            logger.info(
                "[AEGIS][RECOVERED][%s] verified=true | time=%.1fs | latency %.1f->%.1fms | loss %.1f->%.1f%% | health %.1f->%.1f",
                target["device_id"].upper(), recovery_time,
                incident["before"]["latency_ms"], target["latency_ms"],
                incident["before"]["packet_loss_percent"], target["packet_loss_percent"],
                incident["before_health"], after_health,
            )
            self.console(
                "SUCCESS", f"RECOVERED/{target['device_id'].upper()}",
                f"verified=true | time={recovery_time:.1f}s | latency {incident['before']['latency_ms']:.1f}->{target['latency_ms']:.1f}ms | "
                f"loss {incident['before']['packet_loss_percent']:.1f}->{target['packet_loss_percent']:.1f}% | "
                f"health {incident['before_health']:.1f}->{after_health:.1f}",
            )
            self.successful_recoveries += 1
            self.active_incident = None
        elif elapsed > 12:
            # Safety fallback: roll back simulated routing state and return to known baseline.
            self.simulator.restore()
            db.update_incident(incident["id"], "rolled_back", target, round(elapsed, 2))
            db.add_action(incident["id"], target["device_id"], incident["action"]["action"], "rolled_back", "Verification failed; restored safe baseline.")
            db.add_event("recovery_rollback", "Verification failed; simulated action rolled back.", "ERROR", target["device_id"], incident["id"])
            logger.error("[AEGIS][ROLLBACK][%s] recovery verification failed; safe baseline restored", target["device_id"].upper())
            self.console("ERROR", f"ROLLBACK/{target['device_id'].upper()}", "Recovery verification failed; safe baseline restored")
            self.active_incident = None

    def payload(self) -> dict:
        return {
            "type": "network_update", "status": self.status(), "telemetry": self.telemetry,
            "topology": self.simulator.topology(), "prediction": self.latest_prediction,
            "risk": self.latest_risk, "diagnosis": self.latest_diagnosis,
            "events": db.query("system_events", 30), "incidents": db.query("incidents", 10),
            "backend_console": list(self.backend_logs),
        }


runtime = Runtime()


@asynccontextmanager
async def lifespan(_: FastAPI):
    runtime.initialize()
    runtime.telemetry = runtime.simulator.snapshot()
    runtime.task = asyncio.create_task(runtime.loop())
    yield
    if runtime.task:
        runtime.task.cancel()
        try:
            await runtime.task
        except asyncio.CancelledError:
            pass


app = FastAPI(title="AI Self-Healing Network API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)


@app.get("/api/network/status")
def network_status():
    return runtime.status()


@app.get("/api/devices")
def devices():
    return runtime.simulator.topology()


@app.get("/api/telemetry")
def telemetry(limit: int = Query(100, ge=1, le=1000), device_id: str | None = None):
    return db.query("telemetry", limit, device_id)


@app.get("/api/anomalies")
def anomalies(limit: int = Query(100, ge=1, le=1000)):
    return [row for row in db.query("predictions", limit) if row["predicted_failure"] != "normal"]


@app.get("/api/incidents")
def incidents(limit: int = Query(100, ge=1, le=1000)):
    return db.query("incidents", limit)


@app.get("/api/healing-actions")
def healing_actions(limit: int = Query(100, ge=1, le=1000)):
    return db.query("healing_actions", limit)


@app.get("/api/events")
def events(limit: int = Query(100, ge=1, le=1000)):
    return db.query("system_events", limit)


@app.get("/api/model/metrics")
def model_metrics():
    path = MODEL_DIR / "metrics.json"
    if not path.exists():
        raise HTTPException(503, "Models have not been trained. Run python -m backend.ml.train_model.")
    return json.loads(path.read_text(encoding="utf-8"))


@app.post("/api/fault/inject")
def inject_fault(request: FaultRequest):
    if runtime.active_incident:
        raise HTTPException(409, "Wait for the active recovery sequence to finish.")
    try:
        fault = runtime.simulator.inject_fault(request.fault_type, request.device_id)
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    runtime.latest_prediction = None
    runtime.latest_diagnosis = None
    db.add_event("fault_injected", f"Demo fault injected: {request.fault_type.replace('_', ' ')}", "WARNING", request.device_id)
    logger.warning(
        "[AEGIS][DEMO][%s] fault injected=%s | simulated=true | gradual_degradation=true",
        request.device_id.upper(), request.fault_type.upper(),
    )
    runtime.console("WARNING", f"DEMO/{request.device_id.upper()}", f"fault injected={request.fault_type.upper()} | simulated=true | gradual_degradation=true")
    return {"message": "Simulated fault injection started", "fault": fault}


@app.post("/api/fault/restore")
def restore_network():
    runtime.simulator.restore()
    if runtime.active_incident:
        db.update_incident(runtime.active_incident["id"], "manually_restored")
        runtime.active_incident = None
    db.add_event("manual_restore", "Network restored to simulated baseline.", "INFO")
    logger.info("[AEGIS][DEMO] Manual restore completed; simulator returned to healthy baseline")
    runtime.console("INFO", "DEMO", "Manual restore completed; simulator returned to healthy baseline")
    return {"message": "Simulated network restored"}


@app.post("/api/healing/execute")
async def execute_healing(request: HealingRequest):
    severity = "MEDIUM" if request.force and request.severity == "LOW" else request.severity
    result = await runtime.execute_healing(request.device_id, request.failure_type, severity, None)
    if not result["approved"]:
        raise HTTPException(409, result["reason"])
    return result


@app.websocket("/ws/telemetry")
async def telemetry_socket(socket: WebSocket):
    await runtime.sockets.connect(socket)
    try:
        await socket.send_json(runtime.payload())
        while True:
            await socket.receive_text()
    except WebSocketDisconnect:
        runtime.sockets.disconnect(socket)
    except Exception:
        runtime.sockets.disconnect(socket)
