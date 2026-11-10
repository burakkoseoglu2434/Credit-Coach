from fastapi.testclient import TestClient

from credit_coach.app import app

client = TestClient(app)


def test_health_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok", "version": "0.1.0"}


def test_openapi_has_health():
    assert "/health" in app.openapi()["paths"]
