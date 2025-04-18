import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

try:
    # Try package-level imports first (for app running as a module)
    from exitbot.app.api import auth, interview, reports
    from exitbot.app.core.config import settings
except ImportError:
    # Fall back to relative imports (for direct script execution)
    from app.api import auth, interview, reports
    from app.core.config import settings

app = FastAPI(
    title="ExitBot API",
    description="HR Exit Interview Bot with Ollama",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(interview.router, prefix="/api/interviews", tags=["Interviews"])
app.include_router(reports.router, prefix="/api/reports", tags=["Reports"])

@app.get("/", tags=["Health"])
async def health_check():
    """
    Health check endpoint to verify the API is running.
    """
    return {"status": "ok", "message": "ExitBot API is running"}

@app.get("/api/health", tags=["Health"])
async def api_health_check():
    """
    Health check endpoint for Docker container health checks.
    """
    return {"status": "healthy"}

def start():
    """Launched with `poetry run start` at root level or in Docker"""
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    workers = int(os.getenv("WORKERS", "1"))
    reload = os.getenv("ENVIRONMENT", "development").lower() == "development"
    
    uvicorn.run(
        "exitbot.main:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers,
        log_level=log_level,
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 