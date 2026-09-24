from backend.healing.healing_engine import HealingEngine, severity_for
from backend.healing.root_cause import analyze


def test_root_cause_is_explainable():
    row = {"device_id": "r1", "bandwidth_utilization": 96, "interface_utilization": 98, "latency_ms": 180, "packet_loss_percent": 12}
    result = analyze(row, "congestion", 0.91)
    assert result["detected_problem"] == "Network congestion"
    assert result["relevant_metrics"]["latency_ms"] == 180


def test_healing_decision_and_cooldown():
    engine = HealingEngine(cooldown_seconds=60)
    first = engine.select("link_failure", "r1", "CRITICAL")
    assert first["approved"] and first["action"] == "activate_backup_link"
    engine.mark_executed("r1", first["action"])
    second = engine.select("link_failure", "r1", "CRITICAL")
    assert not second["approved"] and "cooldown" in second["reason"].lower()


def test_severity_uses_network_impact():
    row = {"packet_loss_percent": 90, "latency_ms": 400, "device_status": "offline"}
    assert severity_for(row, 0.99) == "CRITICAL"

