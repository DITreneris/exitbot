from typing import Optional
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .api_utils import APIException
from .db.base import get_db
from .db.models import User
from .db import crud

# Configuration
SECRET_KEY = "your-secret-key-here"  # TODO: Move to environment variables
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    credentials_exception = APIException(
        message="Could not validate credentials",
        status_code=status.HTTP_401_UNAUTHORIZED,
        error_code="INVALID_CREDENTIALS",
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception

    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    # if not current_user.is_active:  # Removed check as is_active is removed from User model
    #     raise APIException(
    #         message="Inactive user",
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         error_code="INACTIVE_USER"
    #     )
    return current_user
