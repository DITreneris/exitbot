import time
import logging
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

try:
    # Try package-level imports first
    from exitbot.app.config import settings
except ImportError:
    # Fall back to relative imports
    from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def wait_for_database():
    """Wait for database to be available"""
    retries = 30
    engine = create_engine(settings.DATABASE_URL)
    
    for attempt in range(retries):
        try:
            # Attempt to connect to the database
            with engine.connect() as conn:
                logger.info("Database is ready!")
                return True
        except OperationalError:
            logger.info(f"Database not ready yet, waiting... (attempt {attempt+1}/{retries})")
            time.sleep(2)
    
    logger.error("Could not connect to database after multiple attempts")
    return False

if __name__ == "__main__":
    logger.info("Checking database connection...")
    if not wait_for_database():
        exit(1)
    exit(0) 