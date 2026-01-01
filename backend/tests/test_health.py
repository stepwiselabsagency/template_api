from app.main import create_app
from fastapi.testclient import TestClient


def test_health() -> None:
    app = create_app()
    client = TestClient(app)
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
