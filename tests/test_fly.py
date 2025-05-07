from fastapi.testclient import TestClient

from beaverhabits.main import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    # assert response.json() == {"msg": "Hello World"}
