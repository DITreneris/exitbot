"""
Database initialization script
"""
import logging
import sys
from pathlib import Path

# Add the parent directory to sys.path to make exitbot package importable
parent_dir = str(Path(__file__).parent.parent.parent.parent)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from exitbot.app.core.logging import get_logger
from exitbot.app.db.base import Base, engine
from exitbot.app.db.models import User, Interview, Question, Response

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
            logger.info(f"Found {len(existing_questions)} existing questions, skipping creation")
            return
        
        # Create default questions
        for i, question_text in enumerate(DEFAULT_QUESTIONS):
            crud.create_question(db, {
                "text": question_text,
                "order_num": i + 1,
                "category": "default",
                "is_active": True
            })
        
        logger.info(f"Created {len(DEFAULT_QUESTIONS)} default questions")
    finally:
        db.close()

def create_admin_user():
    """Create an admin user if none exists"""
    import os
    from exitbot.app.core.config import settings
    from exitbot.app.db.base import SessionLocal
    from exitbot.app.db import crud
    
    # Skip admin user creation if settings are missing
    admin_email = getattr(settings, "FIRST_ADMIN_EMAIL", "admin@example.com")
    admin_password = getattr(settings, "FIRST_ADMIN_PASSWORD", "admin")
    
    if not hasattr(crud, "get_password_hash"):
        logger.warning("Password hashing function not found, using plaintext password")
        password_hash = admin_password
    else:
        password_hash = crud.get_password_hash(admin_password)
    
    logger.info("Checking for admin user...")
    db = SessionLocal()
    try:
        # Check if admin user exists
        admin_user = crud.get_user_by_email(db, admin_email)
        
        if admin_user:
            logger.info(f"Admin user {admin_email} already exists")
            return
        
        # Create admin user
        admin_data = {
            "email": admin_email,
            "full_name": "Admin User",
            "hashed_password": password_hash,
            "is_admin": True
        }
        crud.create_user(db, admin_data)
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