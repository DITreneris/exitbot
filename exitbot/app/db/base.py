from sqlalchemy import create_engine

# from sqlalchemy.ext.declarative import declarative_base # Old import
from sqlalchemy.orm import sessionmaker, declarative_base  # New import location

from exitbot.app.core.config import settings

# Create SQLAlchemy engine
engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
