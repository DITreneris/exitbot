"""
Main API router with enhanced OpenAPI documentation
"""
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

# Import directly from app.api modules
from app.api import auth, interview as interviews, reports # Use alias for interviews
# Assuming users, admin, dashboard routers might not exist directly here yet.
from app.core.config import settings

# Main API router
api_router = APIRouter(
    responses={
        401: {"description": "Unauthorized - Authentication required"},
        403: {"description": "Forbidden - Insufficient permissions"},
        404: {"description": "Not Found - Resource not found"},
        422: {"description": "Validation Error - Invalid request parameters"},
        500: {"description": "Internal Server Error - Something went wrong on the server"}
    }
)

# Include all endpoint routers
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["authentication"],
    responses={
        401: {"description": "Invalid credentials or token"},
        403: {"description": "Inactive user account"}
    }
)

# Commented out potentially incorrect includes
# api_router.include_router(
#     users.router, 
#     prefix="/users", 
#     tags=["users"],
#     responses={...}
# )

api_router.include_router(
    interviews.router, # Use alias
    prefix="/interviews",
    tags=["interviews"],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Not authorized to access this interview"},
        404: {"description": "Interview not found"}
    }
)

# api_router.include_router(
#     admin.router,
#     prefix="/admin",
#     tags=["admin"],
#     responses={...}
# )
# 
# api_router.include_router(
#     dashboard.router,
#     prefix="/dashboard",
#     tags=["dashboard"],
#     responses={...}
# )

# Include reports router
api_router.include_router(
    reports.router,
    prefix="/reports",
    tags=["reports"],
    # Assuming reports need admin access based on functions inside reports.py
    dependencies=[Depends(auth.get_current_admin)],
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Admin privileges required"}
    }
)

# Health check endpoint
@api_router.get(
    "/health", 
    tags=["health"],
    summary="Health Check", 
    description="Check the health status of the API",
    response_description="Returns the health status of the API",
    responses={
        200: {
            "description": "API is healthy",
            "content": {
                "application/json": {
                    "example": {"status": "ok"}
                }
            }
        }
    }
)
async def health_check():
    """Simple health check endpoint"""
    return {"status": "ok"}

# API documentation redirect
@api_router.get(
    "/",
    include_in_schema=False
)
async def docs_redirect():
    """Redirect to the API documentation"""
    return RedirectResponse(url=f"{settings.API_V1_PREFIX}/docs") 