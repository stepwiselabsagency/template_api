from __future__ import annotations

from app.api.v1.routes.health import router as health_router
from app.api.v1.routes.users import router as users_router
from fastapi import APIRouter

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(health_router)
v1_router.include_router(users_router)
