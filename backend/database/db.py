from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from backend.config import DB_PATH


SCHEMA = """
CREATE TABLE IF NOT EXISTS devices (
  id TEXT PRIMARY KEY, name TEXT NOT NULL, type TEXT NOT NULL, status TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS telemetry (
  id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL, device_id TEXT NOT NULL,
  payload TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_telemetry_device_time ON telemetry(device_id, timestamp DESC);
CREATE TABLE IF NOT EXISTS incidents (
  id INTEGER PRIMARY KEY AUTOINCREMENT, started_at TEXT NOT NULL, resolved_at TEXT,
  device_id TEXT NOT NULL, failure_type TEXT NOT NULL, severity TEXT NOT NULL,
  status TEXT NOT NULL, diagnosis TEXT NOT NULL, before_metrics TEXT NOT NULL,
  after_metrics TEXT, recovery_time_seconds REAL
);
CREATE TABLE IF NOT EXISTS predictions (
  id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL, device_id TEXT NOT NULL,
  predicted_failure TEXT NOT NULL, confidence REAL NOT NULL, probabilities TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS healing_actions (
  id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL, incident_id INTEGER,
  device_id TEXT NOT NULL, action TEXT NOT NULL, status TEXT NOT NULL, details TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS system_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT NOT NULL, level TEXT NOT NULL,
  event_type TEXT NOT NULL, message TEXT NOT NULL, device_id TEXT, incident_id INTEGER
);
"""


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def connection():
    db = sqlite3.connect(DB_PATH, timeout=10)
    db.row_factory = sqlite3.Row
    try:
        yield db
        db.commit()
    finally:
        db.close()


def init_db(devices: list[dict]) -> None:
    with connection() as db:
        db.executescript(SCHEMA)
        db.executemany(
            "INSERT OR REPLACE INTO devices(id,name,type,status) VALUES(?,?,?,?)",
            [(d["id"], d["name"], d["type"], d.get("status", "healthy")) for d in devices],
        )


def insert_telemetry(rows: list[dict]) -> None:
    with connection() as db:
        db.executemany(
            "INSERT INTO telemetry(timestamp,device_id,payload) VALUES(?,?,?)",
            [(r["timestamp"], r["device_id"], json.dumps(r)) for r in rows],
        )


def create_incident(device_id: str, failure_type: str, severity: str, diagnosis: dict, before: dict) -> int:
    with connection() as db:
        cursor = db.execute(
            "INSERT INTO incidents(started_at,device_id,failure_type,severity,status,diagnosis,before_metrics) VALUES(?,?,?,?,?,?,?)",
            (now(), device_id, failure_type, severity, "diagnosing", json.dumps(diagnosis), json.dumps(before)),
        )
        return int(cursor.lastrowid)


def update_incident(incident_id: int, status: str, after: dict | None = None, recovery_time: float | None = None) -> None:
    with connection() as db:
        if after is None:
            db.execute("UPDATE incidents SET status=? WHERE id=?", (status, incident_id))
        else:
            db.execute(
                "UPDATE incidents SET status=?,resolved_at=?,after_metrics=?,recovery_time_seconds=? WHERE id=?",
                (status, now(), json.dumps(after), recovery_time, incident_id),
            )


def add_prediction(device_id: str, prediction: dict) -> None:
    with connection() as db:
        db.execute(
            "INSERT INTO predictions(timestamp,device_id,predicted_failure,confidence,probabilities) VALUES(?,?,?,?,?)",
            (now(), device_id, prediction["predicted_failure"], prediction["confidence"], json.dumps(prediction["probabilities"])),
        )


def add_action(incident_id: int | None, device_id: str, action: str, status: str, details: str) -> None:
    with connection() as db:
        db.execute(
            "INSERT INTO healing_actions(timestamp,incident_id,device_id,action,status,details) VALUES(?,?,?,?,?,?)",
            (now(), incident_id, device_id, action, status, details),
        )


def add_event(event_type: str, message: str, level: str = "INFO", device_id: str | None = None, incident_id: int | None = None) -> None:
    with connection() as db:
        db.execute(
            "INSERT INTO system_events(timestamp,level,event_type,message,device_id,incident_id) VALUES(?,?,?,?,?,?)",
            (now(), level, event_type, message, device_id, incident_id),
        )


def query(table: str, limit: int = 100, device_id: str | None = None) -> list[dict]:
    allowed = {"telemetry", "incidents", "predictions", "healing_actions", "system_events", "devices"}
    if table not in allowed:
        raise ValueError("Invalid table")
    with connection() as db:
        sql = f"SELECT * FROM {table}"
        params: list = []
        if device_id and table != "devices":
            sql += " WHERE device_id=?"
            params.append(device_id)
        order = "id DESC" if table != "devices" else "id"
        sql += f" ORDER BY {order} LIMIT ?"
        params.append(max(1, min(limit, 1000)))
        rows = [dict(row) for row in db.execute(sql, params).fetchall()]
    json_fields = {"payload", "diagnosis", "before_metrics", "after_metrics", "probabilities"}
    for row in rows:
        for field in json_fields & row.keys():
            if row[field]:
                row[field] = json.loads(row[field])
    return rows
