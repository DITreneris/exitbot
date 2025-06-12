"""
ExitBot - AI-powered exit interview assistant (simplified version)
"""
# Remove unused logging
# import logging
# Remove unused Path
# from pathlib import Path

import uvicorn

# Remove unused Depends, HTTPException
# from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager
import time
from prometheus_fastapi_instrumentator import Instrumentator

# Remove unused StaticFiles
# from fastapi.staticfiles import StaticFiles

from exitbot.app.core.config import settings

# Remove unused setup_logging, get_logger
# from exitbot.app.core.logging import setup_logging, get_logger
from exitbot.app.core.logging import get_logger # Correct import
from exitbot.app.api.api import api_router

# --- Load .env file ---
# Remove unused os
# import os

# load_dotenv() searches for .env in current and parent directories
# This is generally preferred unless you have a very non-standard setup.
# load_dotenv() # Removed call from main.py (should be handled by config now)
# print("Attempted to load .env file.") # Removed print statement

# --- End .env loading ---

# Now import modules that rely on environment variables

# Configure logging
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

from sqlalchemy.orm import Session

from exitbot.app.db.init import init_db

# --- Lifespan Management ---
# Combine startup logic into the lifespan context manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup...")

    # 1. Initialize database
    try:
        # 1.1. Initialize database
        init_db()
        logger.info("Database initialized successfully.")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}", exc_info=True)
        # Depending on the DB strategy, you might want to raise the exception
        # or handle it differently to allow the app to start partially.

    # 2. Expose Prometheus metrics (moved from _startup)
    instrumentator.expose(app)
    logger.info("Prometheus metrics exposed at /metrics")

    # 3. Log registered routes (moved from log_registered_routes)
    logger.info("--- Registered API Routes ---")
    route_list = []
    for route in app.routes:
        if hasattr(route, "path") and route.path.startswith(settings.API_V1_PREFIX):
            methods = ",".join(route.methods) if hasattr(route, "methods") else ""
            route_list.append(
                f"  Path: {route.path}, Methods: [{methods}], Name: {route.name}"
            )
        elif hasattr(route, "path"):
            methods = ",".join(route.methods) if hasattr(route, "methods") else ""
            route_list.append(
                f"  Path: {route.path}, Methods: [{methods}], Name: {route.name}"
            )
    route_list.sort()
    for route_info in route_list:
        logger.info(route_info)
    logger.info("--- End Registered API Routes ---")

    yield  # Application runs here

    # --- Shutdown Logic ---
    logger.info("Application shutdown...")
    # Cleanup resources (e.g., close database connections)


# --- End Lifespan Management ---

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="ExitBot API for conducting automated exit interviews.",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan,
)

# Set up CORS middleware
origins = [
    "http://localhost",  # TODO: Replace with actual frontend URL in production
    "http://localhost:8080",  # Example if frontend runs on a different port
    # Add more origins as needed
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request Logging Middleware - Comment out for testing to avoid NameError
# @app.middleware("http")
# async def log_requests(request: Request, call_next):
#     start_time = time.time()
#     logger.info(f"Request started: {request.method} {request.url.path}")
#     response = await call_next(request)
#     process_time = time.time() - start_time
#     logger.info(
#         f"Request finished: {request.method} {request.url.path} - Status: {response.status_code} - Time: {process_time:.4f}s"
#     )
#     return response


# Include API router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Prometheus Metrics
instrumentator = Instrumentator().instrument(app)


@app.get("/")
async def root():
    """Root endpoint with health check"""
    logger.debug("Root endpoint called.")
    return {"status": "ok", "message": "ExitBot API is running", "version": "1.0.0"}


@app.get("/api")
async def api_root():
    """API root endpoint - redirects to documentation"""
    return RedirectResponse(url="/api/docs")


@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "ok"}


# Example endpoint
@app.get("/api/example")
async def example_endpoint():
    """Example endpoint for testing"""
    return {
        "status": "ok",
        "data": {
            "interviews_conducted": 157,
            "active_users": 42,
            "satisfaction_score": 4.8,
        },
    }


def start():
    """Launched with `poetry run start` at root level"""
    uvicorn.run(
        app,
        host="0.0.0.0",  # Use 0.0.0.0 to make it accessible from other machines
        port=8000,
        log_level="info",
    )


if __name__ == "__main__":
    start()
