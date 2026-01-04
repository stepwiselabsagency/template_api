"""
Pytest entrypoint for shared fixtures.

We keep fixtures small and modular under `backend/tests/fixtures/` and import
them here so pytest can discover them.
"""

# ruff: noqa: F401,F403

from backend.tests.fixtures.auth import *  # noqa: F403
from backend.tests.fixtures.db import *  # noqa: F403
from backend.tests.fixtures.env import *  # noqa: F403
from backend.tests.fixtures.fastapi_app import *  # noqa: F403
from backend.tests.fixtures.redis import *  # noqa: F403
