"""
Authentication API endpoints for user login and token management
"""
import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ...schemas.user import UserInDB  # Direct import
from ...schemas.token import Token  # Direct import
from ...core import security  # Corrected relative import
from ...core.config import settings  # Corrected relative import
from ...db.database import get_db  # Corrected: Use database.py
from ...db.models import User  # Correct path to db models
from ..deps import get_current_active_user # Changed to relative import
from ...db import crud # Added import for crud
from ...core.security import verify_password # Added import for verify_password

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    "/login/access-token", 
    response_model=Token,  # Updated reference
    summary="Login and get access token",
    description="""
    OAuth2 compatible token login, get an access token for future requests.
    Requires valid email and password credentials.
    """,
    response_description="Access token for authentication",
    responses={
        200: {"description": "Successful login, token returned"},
        401: {"description": "Incorrect email or password"},
        422: {"description": "Validation error in credentials"}
    }
)
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login, get an access token for future requests
    
    Args:
        form_data: OAuth2 form with username/password
        db: Database session
        
    Returns:
        Access token
    """
    # OAuth2 uses username, but we're using email
    email = form_data.username
    password = form_data.password
    
    # Fetch user by email
    user = crud.get_user_by_email(db, email=email)
    
    # Verify user existence and password
    if not user or not verify_password(password, user.hashed_password):
        logger.warning(f"Failed login attempt for email: {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Update last login time (optional, consider adding this)
    # crud.update_user_last_login(db, user_id=user.id)
        
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject_email=user.email,  # Pass email as subject
        is_admin=user.is_admin,    # Pass is_admin flag
        expires_delta=access_token_expires
    )
    
    logger.info(f"User {user.id} ({user.email}) logged in successfully")
    return {"access_token": access_token, "token_type": "bearer"}

@router.post(
    "/login/test-token", 
    response_model=UserInDB,  # Updated reference
    summary="Test access token",
    description="""
    Test access token validity and get current user information.
    Used for testing authentication and verifying token.
    """,
    response_description="Current user information",
    responses={
        200: {"description": "Valid token, user information returned"},
        401: {"description": "Invalid or expired token"}
    }
)
async def test_token(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Test access token and get current user
    
    Args:
        current_user: Current authenticated user from token
        
    Returns:
        Current user information
    """
    return current_user 