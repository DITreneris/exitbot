from fastapi import APIRouter

from .endpoints import interviews, auth, users, dashboard

api_router = APIRouter()

# Include routers from endpoints
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(interviews.router, prefix="/interviews", tags=["interviews"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
