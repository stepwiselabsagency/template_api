from __future__ import annotations

import pytest
from app.core.config import get_settings


@pytest.fixture(autouse=True)
def _isolate_test_env(monkeypatch: pytest.MonkeyPatch):
    """
    Keep tests hermetic and consistent:
    - Do not depend on a developer's local `.env`
    - Do not require DB/Redis unless a specific test opts in
    - Avoid cross-test contamination from cached settings
    """

    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key")
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("REDIS_URL", "")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
