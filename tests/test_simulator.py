from backend.network.simulator import NetworkSimulator
from backend.network.telemetry import FEATURES


def test_telemetry_has_required_fields_and_ranges():
    rows = NetworkSimulator().snapshot()
    assert len(rows) == 8
    assert all(feature in rows[0] for feature in FEATURES)
    assert 0 <= rows[0]["packet_loss_percent"] <= 100


def test_congestion_gradually_degrades_metrics():
    simulator = NetworkSimulator(seed=7)
    simulator.inject_fault("congestion", "r1")
    samples = []
    for _ in range(7):
        samples.append(next(row for row in simulator.snapshot() if row["device_id"] == "r1"))
    assert samples[-1]["bandwidth_utilization"] > samples[0]["bandwidth_utilization"]
    assert samples[-1]["latency_ms"] > samples[0]["latency_ms"]


def test_restore_returns_all_devices_to_healthy():
    simulator = NetworkSimulator()
    simulator.inject_fault("link_failure", "r1")
    simulator.snapshot()
    simulator.restore()
    assert all(device["status"] == "healthy" for device in simulator.topology()["devices"])

