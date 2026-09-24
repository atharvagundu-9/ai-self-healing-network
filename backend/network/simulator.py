from __future__ import annotations

import random
from dataclasses import asdict, dataclass
from threading import RLock

from .telemetry import Telemetry


@dataclass(frozen=True)
class Device:
    id: str
    name: str
    type: str
    x: int
    y: int
    redundant: str | None = None


DEVICES = [
    Device("r1", "Edge Router R1", "router", 50, 12, "r2"),
    Device("r2", "Backup Router R2", "router", 78, 28, "r1"),
    Device("core1", "Core Switch", "core_switch", 50, 36),
    Device("sw1", "Access Switch A", "access_switch", 25, 58, "sw2"),
    Device("sw2", "Access Switch B", "access_switch", 70, 58, "sw1"),
    Device("app1", "Application Server", "server", 58, 82, "db1"),
    Device("db1", "Database Server", "database", 83, 82, "app1"),
    Device("client1", "Client Lab", "client", 15, 82),
]

LINKS = [
    ("internet", "r1"), ("internet", "r2"), ("r1", "core1"), ("r2", "core1"),
    ("core1", "sw1"), ("core1", "sw2"), ("sw1", "client1"),
    ("sw2", "app1"), ("sw2", "db1"),
]


class NetworkSimulator:
    """Thread-safe stateful simulator with gradual faults and recovery."""

    VALID_FAULTS = {
        "high_latency", "packet_loss", "congestion", "device_overload",
        "device_failure", "link_failure", "traffic_spike",
    }

    def __init__(self, seed: int = 42) -> None:
        self.random = random.Random(seed)
        self.lock = RLock()
        self.tick_count = 0
        self.fault: dict | None = None
        self.healing: dict | None = None
        self.device_status = {device.id: "healthy" for device in DEVICES}

    def inject_fault(self, fault_type: str, device_id: str = "r1") -> dict:
        if fault_type not in self.VALID_FAULTS:
            raise ValueError(f"Unknown fault type: {fault_type}")
        if device_id not in self.device_status:
            raise ValueError(f"Unknown device: {device_id}")
        with self.lock:
            self.fault = {"type": fault_type, "device_id": device_id, "progress": 0}
            self.healing = None
            self.device_status[device_id] = "warning"
            return dict(self.fault)

    def apply_healing(self, action: str, device_id: str) -> None:
        with self.lock:
            self.healing = {"action": action, "device_id": device_id, "progress": 0}
            self.device_status[device_id] = "healing"

    def restore(self) -> None:
        with self.lock:
            self.fault = None
            self.healing = None
            self.device_status = {device.id: "healthy" for device in DEVICES}

    def snapshot(self) -> list[dict]:
        with self.lock:
            self.tick_count += 1
            if self.fault:
                self.fault["progress"] = min(10, self.fault["progress"] + 1)
            if self.healing:
                self.healing["progress"] += 1
            rows = [self._telemetry_for(device).to_dict() for device in DEVICES]
            if self.healing and self.healing["progress"] >= 5:
                healed = self.healing["device_id"]
                self.device_status[healed] = "healthy"
                self.fault = None
                self.healing = None
            return rows

    def _telemetry_for(self, device: Device) -> Telemetry:
        r = self.random
        latency = r.uniform(14, 28)
        loss = r.uniform(0.0, 0.8)
        bandwidth = r.uniform(28, 55)
        throughput = r.uniform(120, 280)
        jitter = r.uniform(1.2, 4.5)
        cpu = r.uniform(24, 49)
        memory = r.uniform(31, 58)
        errors = r.uniform(0.0, 0.5)
        interface = bandwidth + r.uniform(-4, 4)
        failure = "normal"
        status = self.device_status[device.id]

        if self.fault and self.fault["device_id"] == device.id:
            p = self.fault["progress"] / 10
            failure = self.fault["type"]
            status = "critical" if p >= 0.8 else "warning"
            if failure == "congestion":
                bandwidth += 50 * p; interface += 48 * p; latency += 150 * p; loss += 11 * p; jitter += 25 * p; throughput -= 70 * p
            elif failure == "high_latency":
                latency += 190 * p; jitter += 20 * p
            elif failure == "packet_loss":
                loss += 22 * p; errors += 8 * p; jitter += 12 * p
            elif failure == "device_overload":
                cpu += 60 * p; memory += 48 * p; latency += 80 * p; throughput -= 50 * p
            elif failure == "device_failure":
                loss += 100 * p; throughput *= max(0, 1 - p); latency += 250 * p
            elif failure == "link_failure":
                loss += 95 * p; errors += 30 * p; interface *= max(0, 1 - p); throughput *= max(0, 1 - p)
            elif failure == "traffic_spike":
                bandwidth += 65 * p; interface += 60 * p; throughput += 300 * p; cpu += 35 * p; latency += 80 * p

        if self.healing and self.healing["device_id"] == device.id:
            factor = max(0.05, 1 - self.healing["progress"] / 5)
            latency = 22 + (latency - 22) * factor
            loss = 0.5 + (loss - 0.5) * factor
            bandwidth = 42 + (bandwidth - 42) * factor
            interface = 40 + (interface - 40) * factor
            cpu = 36 + (cpu - 36) * factor
            memory = 44 + (memory - 44) * factor
            errors *= factor
            jitter = 2.5 + (jitter - 2.5) * factor
            status = "healing"

        if failure in {"device_failure", "link_failure"} and self.fault and self.fault["progress"] >= 9:
            status = "offline"

        bounded = lambda value, hi=100: round(max(0, min(hi, value)), 2)
        return Telemetry.now(
            device.id, device.type,
            latency_ms=bounded(latency, 500), packet_loss_percent=bounded(loss),
            bandwidth_utilization=bounded(bandwidth), throughput_mbps=bounded(throughput, 1000),
            jitter_ms=bounded(jitter, 100), cpu_usage_percent=bounded(cpu),
            memory_usage_percent=bounded(memory), error_rate=bounded(errors),
            interface_utilization=bounded(interface), device_status=status,
            failure_type=failure,
        )

    def topology(self) -> dict:
        return {
            "devices": [{**asdict(device), "status": self.device_status[device.id]} for device in DEVICES],
            "links": [{"source": source, "target": target} for source, target in LINKS],
        }
