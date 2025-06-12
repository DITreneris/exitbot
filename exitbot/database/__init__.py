from exitbot.database.database import Base, engine, get_db, SessionLocal
from exitbot.database.models import User, Question, ExitInterview, Answer, UserRole

# Export all models and database utilities
__all__ = [
    "Base",
    "engine",
    "get_db",
    "SessionLocal",
    "User",
    "Question",
    "ExitInterview",
    "Answer",
    "UserRole",
]


# Initialize database (create tables)
def init_db():
    Base.metadata.create_all(bind=engine)
