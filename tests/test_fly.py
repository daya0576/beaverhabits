from fastapi.testclient import TestClient

from fly.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "OK"


def test_metrics():
    response = client.get("/metrics")
    assert response.status_code == 200


def test_callback():
    response = client.post("/paddle/callback")
    assert response.status_code == 200
