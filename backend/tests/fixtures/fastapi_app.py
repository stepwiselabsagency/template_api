from __future__ import annotations

import os

import pytest
from app.core.config import get_settings
from app.db import get_db
from app.main import create_app
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session


@pytest.fixture()
def app(db_session: Session, database_url: str) -> FastAPI:
    """
    FastAPI app wired to the per-test `db_session`.
    """
    # Opt into DB for endpoints (like readiness) that look at settings.DATABASE_URL.
    os.environ["DATABASE_URL"] = database_url
    get_settings.cache_clear()

    application = create_app()

    def override_get_db():
        yield db_session

    application.dependency_overrides[get_db] = override_get_db
    return application


@pytest.fixture()
def client(app: FastAPI) -> TestClient:
    return TestClient(app)
