from datetime import datetime, timedelta
from typing import Optional

from jose import jwt
from passlib.context import CryptContext

# Use absolute import from project root
from exitbot.app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = "HS256"


def create_access_token(
    subject_email: str,
    is_admin: bool = False,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create access token with email as subject."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {"exp": expire, "sub": subject_email, "is_admin": is_admin}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_employee_token(email: str) -> str:
    """Create a short-lived token for employee interviews"""
    expire = datetime.utcnow() + timedelta(hours=24)
    to_encode = {"exp": expire, "sub": email, "is_admin": False}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
