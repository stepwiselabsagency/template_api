from __future__ import annotations

import os

import pytest
import redis


@pytest.fixture()
def redis_client():
    """
    Optional Redis client for tests that explicitly opt in.

    By default, local tests run with REDIS_URL cleared (see `isolate_test_env`).
    """
    url = os.getenv("REDIS_URL") or ""
    if not url:
        pytest.skip("REDIS_URL not configured")
    client = redis.Redis.from_url(url, decode_responses=True)
    try:
        client.ping()
    except Exception as exc:
        pytest.skip(f"Redis unavailable: {exc}")
    yield client
    try:
        client.flushdb()
    except Exception:
        # Best effort cleanup.
        pass
