from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone


@dataclass(slots=True)
class Telemetry:
    timestamp: str
    device_id: str
    device_type: str
    latency_ms: float
    packet_loss_percent: float
    bandwidth_utilization: float
    throughput_mbps: float
    jitter_ms: float
    cpu_usage_percent: float
    memory_usage_percent: float
    error_rate: float
    interface_utilization: float
    device_status: str = "healthy"
    failure_type: str = "normal"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def now(cls, device_id: str, device_type: str, **metrics: float | str) -> "Telemetry":
        return cls(
            timestamp=datetime.now(timezone.utc).isoformat(),
            device_id=device_id,
            device_type=device_type,
            **metrics,
        )


FEATURES = [
    "latency_ms",
    "packet_loss_percent",
    "bandwidth_utilization",
    "throughput_mbps",
    "jitter_ms",
    "cpu_usage_percent",
    "memory_usage_percent",
    "error_rate",
    "interface_utilization",
]

