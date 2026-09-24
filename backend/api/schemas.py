from typing import Literal

from pydantic import BaseModel, Field


class FaultRequest(BaseModel):
    fault_type: Literal[
        "high_latency", "packet_loss", "congestion", "device_overload",
        "device_failure", "link_failure", "traffic_spike",
    ]
    device_id: str = "r1"


class HealingRequest(BaseModel):
    failure_type: str
    device_id: str = "r1"
    severity: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"] = "HIGH"
    force: bool = Field(default=False, description="Bypass severity only; cooldown still applies")

