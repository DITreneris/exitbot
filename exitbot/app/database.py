from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

try:
    # Try package-level imports first
    from exitbot.app.config import settings
except ImportError:
    # Fall back to relative imports
    from app.config import settings

SQLALCHEMY_DATABASE_URI = settings.DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URI)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
