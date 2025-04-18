from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy.orm import Session

# Use absolute import from project root
from exitbot.app.core.config import settings
from exitbot.app.core.security import (
    create_access_token,
    create_employee_token,
    get_password_hash,
    verify_password,
)
from exitbot.app.db import crud
from exitbot.app.db.base import get_db
from exitbot.app.schemas.auth import (
    Token,
    TokenData,
    User,
    UserCreate,
    LoginRequest,
    EmployeeAccessRequest,
)

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Validate the token and return the current user
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        email: str = payload.get("sub")
        is_admin: bool = payload.get("is_admin", False)
        
        if email is None:
            raise credentials_exception
            
        token_data = TokenData(email=email, is_admin=is_admin)
    except JWTError:
        raise credentials_exception
        
    user = crud.get_user_by_email(db, email=token_data.email)
    if user is None:
        raise credentials_exception
        
    return user

async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Check if the current user is an admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return current_user

@router.post("/login", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> Any:
    """
    OAuth2 compatible token login, get an access token for future requests
    """
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Update last login time
    crud.update_user_last_login(db, user_id=user.id)
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.email, is_admin=user.is_admin, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/employee-access", response_model=Token)
async def create_employee_access_token(
    employee_data: EmployeeAccessRequest,
    db: Session = Depends(get_db),
) -> Any:
    """
    Create a one-time access token for an employee to participate in exit interview
    """
    # Check if user exists
    user = crud.get_user_by_email(db, email=employee_data.email)
    
    # If user doesn't exist, create one
    if not user:
        user_in = UserCreate(
            email=employee_data.email,
            full_name=employee_data.full_name,
            department=employee_data.department,
            is_admin=False,
        )
        user = crud.create_user(db, user_in.dict())
    
    # Create token
    access_token = create_employee_token(email=user.email)
    
    return {"access_token": access_token, "token_type": "bearer"} 