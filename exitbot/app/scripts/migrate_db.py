# Remove unused sys
# import sys
# Remove unused os
# import os
# Remove unused importlib
# import importlib
# Remove unused context
# from alembic import context
# Remove unused create_engine, pool
# from sqlalchemy import create_engine, pool
from sqlalchemy.exc import SQLAlchemyError
import logging
import sys
import os

# --- Add project root to sys.path ---
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
# --- End sys.path modification ---

try:
    # Try direct db path imports
    from exitbot.app.db.base import Base # Base is in db.base
    # Import the singleton connection object
    from exitbot.app.db.database import db_connection 
except ImportError:
    # Fallback if structure is different (less likely now)
    # from app.models.users import Base
    # from app.database import engine
    # Add more specific error handling if needed
    raise # Re-raise the original ImportError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def import_all_models():
    """Import all model modules to ensure they're registered with SQLAlchemy"""
    try:
        # Try to import all model modules to ensure they're registered
        # This is a simple version - in a real app you might want to use
        # dynamic imports to find all model modules
        # Dynamically import all modules in the models directory
        # Add more specific imports if needed
        # Removed: from app.models.users import *

        logger.info("All models imported successfully")
    except ImportError as e:
        logger.error(f"Error importing models: {str(e)}")
        raise


def run_migrations():
    """Run Alembic migrations to upgrade the database to the latest revision."""
    logger.info("Starting database migrations using Alembic...")
    try:
        # Use Alembic API to run migrations
        from alembic.config import Config
        from alembic import command
        
        # Assuming alembic.ini is in the project root relative to this script
        # Adjust path if alembic.ini is located elsewhere
        alembic_cfg = Config("alembic.ini") 
        command.upgrade(alembic_cfg, "head")
        logger.info("Alembic migration completed successfully.")
    except Exception as e:
        logger.error(f"Alembic migration failed: {str(e)}")
        raise

# Comment out or remove the old create_all based logic
# def run_migrations_old():
#     """Create all tables in the database"""
#     logger.info("Starting database migrations...")
# 
#     try:
#         # Import all models to ensure they're registered
#         import_all_models()
# 
#         # Create all tables
#         Base.metadata.create_all(bind=engine)
#         logger.info("Database migration completed successfully")
#     except SQLAlchemyError as e:
#         logger.error(f"Database migration failed: {str(e)}")
#         raise


if __name__ == "__main__":
    run_migrations()
