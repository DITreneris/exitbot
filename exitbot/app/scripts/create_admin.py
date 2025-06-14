# import argparse
import logging
from sqlalchemy.orm import Session

# Remove unused os
# import os
# Remove unused sys
# import sys
# Add the parent directory to sys.path FIRST
# ... (keep sys.path logic)

# NOW import other modules
from exitbot.app.core.config import settings

# Removed: from exitbot.app.core.logging import get_logger
from exitbot.app.db.base import SessionLocal  # Keep

# Removed: from exitbot.app.db import crud  # Keep
from exitbot.app.schemas.user import UserCreate  # Keep

try:
    # Try package-level imports first
    from exitbot.app.crud import user as user_crud
except ImportError:
    # Fall back to relative imports
    from app.crud import user as user_crud

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_admin_user(db: Session):
    """Create an admin user if one doesn't exist"""
    # Check if admin user exists
    admin_email = settings.FIRST_ADMIN_EMAIL
    if not admin_email:
        logger.warning("No admin email specified in settings")
        return

    admin = user_crud.get_user_by_email(db, email=admin_email)
    if admin:
        logger.info("Admin user already exists")
        return

    logger.info("Creating admin user...")
    admin_password = settings.FIRST_ADMIN_PASSWORD
    if not admin_password:
        logger.error("Admin password not specified in settings")
        return

    user_in = UserCreate(
        email=admin_email,
        password=admin_password,
        is_superuser=True,
    )

    user = user_crud.create_user(db, obj_in=user_in)
    logger.info(f"Admin user created with email: {user.email}")


def main():
    logger.info("Initializing admin user...")
    db = SessionLocal()
    try:
        create_admin_user(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
