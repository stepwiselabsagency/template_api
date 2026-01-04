from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.mark.integration
def test_health_endpoints(client: TestClient) -> None:
    legacy = client.get("/health")
    assert legacy.status_code == 200
    assert legacy.json() == {"status": "ok"}
    assert legacy.headers.get("X-Request-ID")

    live = client.get("/api/v1/health/live")
    assert live.status_code == 200
    assert live.json() == {"status": "ok"}
    assert live.headers.get("X-Request-ID")

    ready = client.get("/api/v1/health/ready")
    assert ready.status_code == 200
    body = ready.json()
    assert body["status"] == "ok"
    assert body["checks"]["db"] == "ok"
    assert ready.headers.get("X-Request-ID")


@pytest.mark.integration
def test_user_flow_create_login_and_me(client: TestClient) -> None:
    # Create user (v1)
    created = client.post(
        "/api/v1/users",
        json={"email": "it-user@example.com", "password": "pass123"},
    )
    assert created.status_code == 201
    user_id = created.json()["id"]
    assert created.headers.get("X-Request-ID")

    # Login (legacy)
    login = client.post(
        "/auth/login",
        data={"username": "it-user@example.com", "password": "pass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]
    assert login.headers.get("X-Request-ID")

    # Me (v1)
    me = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.headers.get("X-Request-ID")
    me_body = me.json()
    assert me_body["id"] == user_id
    assert me_body["email"] == "it-user@example.com"


@pytest.mark.integration
def test_error_schema_404_includes_request_id(client: TestClient) -> None:
    res = client.get("/api/v1/does-not-exist")
    assert res.status_code == 404
    request_id = res.headers.get("X-Request-ID")
    assert request_id

    body = res.json()
    assert set(body.keys()) == {"error"}
    assert body["error"]["request_id"] == request_id


@pytest.mark.integration
def test_error_schema_422_validation_error_includes_request_id(
    client: TestClient,
) -> None:
    res = client.post("/api/v1/users", json={"email": "bad@example.com"})
    assert res.status_code == 422
    request_id = res.headers.get("X-Request-ID")
    assert request_id

    body = res.json()
    assert set(body.keys()) == {"error"}
    assert body["error"]["request_id"] == request_id
