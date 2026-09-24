from fastapi.testclient import TestClient

from backend.main import app


def test_status_devices_and_model_metrics_endpoints():
    with TestClient(app) as client:
        status = client.get("/api/network/status")
        assert status.status_code == 200
        assert 0 <= status.json()["network_health"] <= 100
        assert len(client.get("/api/devices").json()["devices"]) == 8
        metrics = client.get("/api/model/metrics")
        assert metrics.status_code == 200
        assert "macro_f1" in metrics.json()


def test_fault_injection_and_restore_endpoints():
    with TestClient(app) as client:
        response = client.post("/api/fault/inject", json={"fault_type": "congestion", "device_id": "r1"})
        assert response.status_code == 200
        assert response.json()["fault"]["type"] == "congestion"
        restored = client.post("/api/fault/restore")
        assert restored.status_code == 200


def test_invalid_device_is_rejected():
    with TestClient(app) as client:
        response = client.post("/api/fault/inject", json={"fault_type": "congestion", "device_id": "unknown"})
        assert response.status_code == 400

