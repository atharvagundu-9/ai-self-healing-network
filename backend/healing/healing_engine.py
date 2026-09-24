from __future__ import annotations

import time


ACTION_MAP = {
    "congestion": "reroute_traffic",
    "high_latency": "reroute_traffic",
    "packet_loss": "restart_interface",
    "device_overload": "redistribute_load",
    "link_failure": "activate_backup_link",
    "device_failure": "switch_to_redundant_device",
    "traffic_spike": "apply_rate_limiting",
}

ACTION_LABELS = {
    "reroute_traffic": "Reroute traffic through backup path",
    "restart_interface": "Restart unstable interface (simulated)",
    "redistribute_load": "Redistribute traffic load",
    "activate_backup_link": "Activate redundant network link",
    "switch_to_redundant_device": "Fail over to redundant device",
    "apply_rate_limiting": "Apply adaptive rate limiting",
}


class HealingEngine:
    def __init__(self, cooldown_seconds: int = 20) -> None:
        self.cooldown_seconds = cooldown_seconds
        self.last_action: dict[tuple[str, str], float] = {}

    def select(self, failure_type: str, device_id: str, severity: str) -> dict:
        action = ACTION_MAP.get(failure_type)
        if not action:
            return {"approved": False, "reason": "No recovery action is required for normal telemetry."}
        key = (device_id, action)
        remaining = self.cooldown_seconds - (time.monotonic() - self.last_action.get(key, -10_000))
        if remaining > 0:
            return {"approved": False, "reason": f"Safety cooldown active for {remaining:.0f} more seconds."}
        if severity == "LOW":
            return {"approved": False, "reason": "Severity is too low for automatic action."}
        return {"approved": True, "action": action, "label": ACTION_LABELS[action]}

    def mark_executed(self, device_id: str, action: str) -> None:
        self.last_action[(device_id, action)] = time.monotonic()


def severity_for(telemetry: dict, confidence: float) -> str:
    loss = telemetry["packet_loss_percent"]
    latency = telemetry["latency_ms"]
    bandwidth = telemetry.get("bandwidth_utilization", 0)
    throughput = telemetry.get("throughput_mbps", 0)
    cpu = telemetry.get("cpu_usage_percent", 0)
    if telemetry["device_status"] == "offline" or loss >= 80:
        return "CRITICAL"
    if loss >= 8 or latency >= 140 or confidence >= 0.9:
        return "HIGH"
    if loss >= 3 or latency >= 75 or bandwidth >= 70 or throughput >= 350 or cpu >= 75 or confidence >= 0.7:
        return "MEDIUM"
    return "LOW"
