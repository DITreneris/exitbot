#!/usr/bin/env python
"""
Debug script to directly test API endpoints
"""
import logging
import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import sys
import os

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create a simple FastAPI app for debugging
app = FastAPI(
    title="ExitBot Debug API",
    description="Debug version of ExitBot API",
    version="1.0.0"
)

@app.get("/")
async def root():
    """Root endpoint"""
    return {"status": "ok", "message": "Debug API is running"}

@app.get("/api/test")
async def test_endpoint():
    """Test endpoint"""
    return {
        "status": "ok",
        "message": "Debug test endpoint is working",
        "data": {
            "test_id": 12345,
            "is_functional": True
        }
    }

@app.get("/api/env")
async def env_info():
    """Return environment information for debugging"""
    return {
        "python_version": sys.version,
        "env_vars": {k: v for k, v in os.environ.items() if not k.startswith("_")},
        "sys_path": sys.path,
        "cwd": os.getcwd()
    }

@app.get("/api/routes")
async def list_routes():
    """List all available routes"""
    routes = []
    for route in app.routes:
        routes.append({
            "path": route.path,
            "name": route.name,
            "methods": route.methods if hasattr(route, "methods") else None
        })
    return {"routes": routes}

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests for debugging"""
    logger.info(f"Request: {request.method} {request.url}")
    try:
        response = await call_next(request)
        logger.info(f"Response status: {response.status_code}")
        return response
    except Exception as e:
        logger.exception("Error processing request")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Server error: {str(e)}"}
        )

if __name__ == "__main__":
    # Run a simple server
    port = 9000
    logger.info(f"Starting debug server on port {port}")
    logger.info(f"Access the debug server at http://127.0.0.1:{port} or http://localhost:{port}")
    logger.info(f"Available endpoints:")
    logger.info(f"  - / (root)")
    logger.info(f"  - /api/test")
    logger.info(f"  - /api/env")
    logger.info(f"  - /api/routes")
    
    uvicorn.run(
        "debug:app",
        host="0.0.0.0",
        port=port,
        log_level="debug"
    ) 