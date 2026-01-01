from app.main import create_app
from fastapi.testclient import TestClient


def test_health() -> None:
    app = create_app()
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
    assert res.headers.get("X-Request-ID")


def test_health_uses_incoming_request_id() -> None:
    app = create_app()
    client = TestClient(app)
    res = client.get("/health", headers={"X-Request-ID": "test-request-id"})
    assert res.status_code == 200
    assert res.headers.get("X-Request-ID") == "test-request-id"
