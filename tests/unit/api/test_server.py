from fastapi.testclient import TestClient

from api.server import app


def test_healthcheck_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
