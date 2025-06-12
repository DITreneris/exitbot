"""
Database initialization script
"""
import sys  # Add sys import
from pathlib import Path  # Add Path import

# import os
# Remove unused Session
# from sqlalchemy.orm import Session

# Add the parent directory to sys.path FIRST
parent_dir = str(Path(__file__).resolve().parent.parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# NOW import other modules
# Removed unused: import logging
from exitbot.app.core.config import settings
from exitbot.app.core.logging import get_logger
from exitbot.app.db.base import Base, engine, SessionLocal
from exitbot.app.db import crud

# Remove E402 error source:
# These should be imported inside functions where needed or moved up if globally required
# from exitbot.app.llm.prompts import DEFAULT_QUESTIONS
# from exitbot.app.core.security import get_password_hash
# from exitbot.app.schemas.user import UserCreate

logger = get_logger("exitbot.db.init")


def init_db():
    """Initialize the database by creating all tables"""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def create_default_questions():
    """Create default interview questions in the database"""
    from exitbot.app.llm.prompts import DEFAULT_QUESTIONS
    from exitbot.app.db.base import SessionLocal
    from exitbot.app.db import crud

    logger.info("Creating default interview questions...")
    db = SessionLocal()
    try:
        # Check if questions already exist
        existing_questions = crud.get_all_questions(db)
        if existing_questions:
            logger.info(
                f"Found {len(existing_questions)} existing questions, skipping creation"
            )
            return

        # Create default questions
        for i, question_text in enumerate(DEFAULT_QUESTIONS):
            crud.create_question(
                db,
                {
                    "text": question_text,
                    "order_num": i + 1,
                    "category": "default",
                    "is_active": True,
                },
            )

        logger.info(f"Created {len(DEFAULT_QUESTIONS)} default questions")
    finally:
        db.close()


def create_admin_user():
    """Create an admin user if none exists"""
    # Skip admin user creation if settings are missing
    admin_email = getattr(settings, "FIRST_ADMIN_EMAIL", "admin@example.com")
    admin_password = getattr(settings, "FIRST_ADMIN_PASSWORD", "admin")

    # We need get_password_hash, UserCreate from schemas, create_user from crud
    # from exitbot.app.core.security import get_password_hash
    from exitbot.app.schemas.user import UserCreate

    # from exitbot.app.db.crud import create_user # Use crud.create_user

    logger.info("Checking for admin user...")
    db = SessionLocal()
    try:
        # We need get_user_by_email from crud
        # from exitbot.app.db.crud import get_user_by_email # Use crud.get_user_by_email
        admin_user = crud.get_user_by_email(db, email=admin_email)

        if admin_user:
            logger.info(f"Admin user {admin_email} already exists")
            return

        # Create admin user
        admin_data = UserCreate(
            email=admin_email,
            full_name="Admin User",
            password=admin_password,  # Pass plain password to UserCreate
            is_admin=True,
        )
        crud.create_user(db, user_in=admin_data)
        logger.info(f"Created admin user: {admin_email}")
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("Initializing database...")
    init_db()
    create_default_questions()
    # Try to create admin user but don't fail if it errors
    try:
        create_admin_user()
    except Exception as e:
        logger.warning(f"Could not create admin user: {str(e)}")
    logger.info("Database initialization complete")
