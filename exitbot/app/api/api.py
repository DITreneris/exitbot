"""
Main API router with enhanced OpenAPI documentation
"""
from fastapi import APIRouter, Depends
from fastapi.responses import RedirectResponse

# Use absolute imports based on project structure
from exitbot.app.api.endpoints import auth, interviews, users, dashboard # Removed reports
# If interview module was indeed meant to be imported as 'interviews', keep that alias
# from app.api import auth, interview as interviews, reports # Old relative import

# Assuming users, admin, dashboard routers might not exist directly here yet.
# from exitbot.app.core.config import settings # Example absolute import
# from exitbot.app.db.database import get_db # Example absolute import

# Main API router
api_router = APIRouter(
    responses={
        401: {"description": "Unauthorized - Authentication required"},
        403: {"description": "Forbidden - Insufficient permissions"},
        404: {"description": "Not Found - Resource not found"},
        422: {"description": "Validation Error - Invalid request parameters"},
        500: {
            "description": "Internal Server Error - Something went wrong on the server"
        },
    }
)

# Include routers from endpoint modules
api_router.include_router(auth.router, tags=["Authentication"])
api_router.include_router(interviews.router, tags=["Interviews"])
api_router.include_router(users.router, tags=["Users"])
# api_router.include_router(reports.router, tags=["Reports"]) # Removed non-existent router
api_router.include_router(dashboard.router, tags=["Dashboard"])
# Add other routers here if needed


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
            "content": {"application/json": {"example": {"status": "ok"}}},
        }
    },
)
async def health_check():
    """Simple health check endpoint"""
    return {"status": "ok"}


# API documentation redirect
@api_router.get("/", include_in_schema=False)
async def docs_redirect():
    """Redirect to the API documentation"""
    return RedirectResponse(url=f"{settings.API_V1_PREFIX}/docs")
