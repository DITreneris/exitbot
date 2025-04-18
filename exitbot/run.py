"""
ExitBot - AI-powered exit interview assistant
Run script for starting the application
"""
import uvicorn
import os
import logging
import sys
from pathlib import Path

# Add the parent directory to sys.path to make exitbot package importable
parent_dir = str(Path(__file__).parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Starting ExitBot application...")
    
    # Get environment variables or use defaults
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    workers = int(os.getenv("WORKERS", "1"))
    log_level = os.getenv("LOG_LEVEL", "info").lower()
    
    logger.info(f"Server will run on {host}:{port}")
    logger.info(f"Configuration: reload={reload}, workers={workers}, log_level={log_level}")
    
    # Start the server
    app_module = "exitbot.direct_app:app"  # Use the working direct application
    logger.info(f"Using app module: {app_module}")
    
    uvicorn.run(
        app_module,
        host=host,
        port=port,
        reload=reload,
        workers=workers,
        log_level=log_level
    ) 