from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

# Import password hashing from core security module
from exitbot.app.core.security import get_password_hash

from exitbot.app.db.models import User

# User operations
def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user_data: Dict[str, Any]) -> User:
    # Hash the password before creating the user
    hashed_password = get_password_hash(user_data["password"])
    db_user = User(
        email=user_data["email"],
        hashed_password=hashed_password,
        full_name=user_data.get("full_name"),
        is_admin=user_data.get("is_admin", False),
        department=user_data.get("department")
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user_last_login(db: Session, user_id: int) -> Optional[User]:
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db_user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(db_user)
    return db_user

# Add get_user_by_username if it doesn't exist
def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.email == username).first() 