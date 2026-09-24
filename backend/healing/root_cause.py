from __future__ import annotations


def analyze(telemetry: dict, predicted_failure: str, model_confidence: float) -> dict:
    """Return an explainable diagnosis backed by the observed metrics."""
    m = telemetry
    causes = {
        "congestion": (
            "Network congestion",
            "Interface and bandwidth utilization are saturated while latency and loss are elevated.",
            ["bandwidth_utilization", "interface_utilization", "latency_ms", "packet_loss_percent"],
        ),
        "device_overload": (
            "Device resource exhaustion",
            "CPU and memory pressure are delaying packet processing.",
            ["cpu_usage_percent", "memory_usage_percent", "latency_ms"],
        ),
        "link_failure": (
            "Failed or disconnected link",
            "Near-total packet loss, low throughput, and interface errors indicate a broken path.",
            ["packet_loss_percent", "throughput_mbps", "error_rate", "interface_utilization"],
        ),
        "device_failure": (
            "Unreachable network device",
            "The node is not forwarding traffic and reports failure-level loss.",
            ["packet_loss_percent", "throughput_mbps", "latency_ms"],
        ),
        "traffic_spike": (
            "Abnormal traffic surge",
            "Throughput and utilization rose sharply with additional CPU pressure.",
            ["throughput_mbps", "bandwidth_utilization", "cpu_usage_percent"],
        ),
        "high_latency": (
            "Excessive path delay",
            "Round-trip latency and jitter exceed the healthy operating range.",
            ["latency_ms", "jitter_ms"],
        ),
        "packet_loss": (
            "Unstable interface or path",
            "Packet loss, error rate, and jitter indicate an unreliable link.",
            ["packet_loss_percent", "error_rate", "jitter_ms"],
        ),
    }
    issue, cause, fields = causes.get(predicted_failure, (
        "No active failure", "Metrics remain inside the learned normal envelope.", ["latency_ms", "packet_loss_percent"]
    ))
    return {
        "detected_problem": issue,
        "probable_cause": cause,
        "confidence": round(model_confidence, 4),
        "affected_device": m["device_id"],
        "relevant_metrics": {field: m[field] for field in fields},
    }

