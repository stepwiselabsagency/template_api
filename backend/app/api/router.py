from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from fastapi import APIRouter

router = APIRouter()

router.include_router(auth_router)
router.include_router(users_router)
