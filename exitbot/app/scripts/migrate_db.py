import logging
import importlib
from sqlalchemy.exc import SQLAlchemyError

try:
    # Try package-level imports first
    from exitbot.app.models.users import Base
    from exitbot.app.database import engine
except ImportError:
    # Fall back to relative imports
    from app.models.users import Base
    from app.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def import_all_models():
    """Import all model modules to ensure they're registered with SQLAlchemy"""
    try:
        # Try to import all model modules to ensure they're registered
        # This is a simple version - in a real app you might want to use
        # dynamic imports to find all model modules
        from app.models import users
        # Import other model modules as needed
        
        logger.info("All models imported successfully")
    except ImportError as e:
        logger.error(f"Error importing models: {str(e)}")
        raise

def run_migrations():
    """Create all tables in the database"""
    logger.info("Starting database migrations...")
    
    try:
        # Import all models to ensure they're registered
        import_all_models()
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database migration completed successfully")
    except SQLAlchemyError as e:
        logger.error(f"Database migration failed: {str(e)}")
        raise

if __name__ == "__main__":
    run_migrations() 