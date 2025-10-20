from fastapi import APIRouter

from app.routes.auth import auth_router
from app.routes.profiles import profile_router
from app.routes.users import user_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(profile_router)
