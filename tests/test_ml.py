from backend.ml.anomaly_detector import AnomalyDetector
from backend.ml.failure_predictor import FailurePredictor


CONGESTED = {
    "device_id": "r1", "latency_ms": 190, "packet_loss_percent": 11,
    "bandwidth_utilization": 97, "throughput_mbps": 92, "jitter_ms": 24,
    "cpu_usage_percent": 68, "memory_usage_percent": 66, "error_rate": 4,
    "interface_utilization": 98,
}


def test_isolation_forest_detects_clear_anomaly():
    result = AnomalyDetector().predict(CONGESTED)
    assert result["is_anomaly"] is True
    assert 0 <= result["anomaly_score"] <= 1


def test_random_forest_classifies_congestion():
    result = FailurePredictor().predict(CONGESTED)
    assert result["predicted_failure"] == "congestion"
    assert result["confidence"] > 0.5
    assert abs(sum(result["probabilities"].values()) - 1) < 0.01


def test_trend_window_reports_risk_without_exact_time_claim():
    predictor = FailurePredictor()
    result = None
    for latency in [20, 30, 48, 78, 120]:
        row = {**CONGESTED, "latency_ms": latency, "packet_loss_percent": latency / 15, "bandwidth_utilization": min(99, 35 + latency / 1.7)}
        result = predictor.failure_risk(row)
    assert result["level"] in {"HIGH", "CRITICAL"}
    assert "monitoring window" in result["message"]

