"""
Dependency injection functions for FastAPI with enhanced validation and error handling
"""
import logging
import time
from typing import Generator, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from pydantic import ValidationError

from ..core.config import settings
from ..core.security import ALGORITHM
from ..db.database import get_db
# from ..models.user import User # Old import path
from ..db.models import User # Correct import path for the User model
from ..schemas.token import TokenPayload

# Configure logger
logger = logging.getLogger(__name__)

# OAuth2 bearer token scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_PREFIX}/auth/login")

def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Get current authenticated user with enhanced validation
    
    Args:
        db: Database session
        token: JWT token
        
    Returns:
        User: Authenticated user model
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Validate token
        if not token:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        try:
            # Decode JWT
            payload = jwt.decode(
                token, settings.SECRET_KEY, algorithms=[ALGORITHM]
            )
            
            # Validate token data
            token_data = TokenPayload(**payload)
            
            # Check token expiration
            if token_data.exp and token_data.exp < int(time.time()):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except ValidationError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from database
        user = db.query(User).filter(User.email == token_data.sub).first()
        if not user:
            logger.warning(f"User with email {token_data.sub} not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error during authentication: {str(e)}")
        # Use the specific error causing the SQL issue if possible, else generic
        # if "no such column: users.is_active" in str(e): # Removed check as column is removed
        #      logger.error(f"Database schema mismatch: users.is_active column missing but queried.")
        #      detail = "Internal server error due to schema mismatch."
        #      status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        # else:
        detail = "Authentication error"
        status_code = status.HTTP_401_UNAUTHORIZED

        raise HTTPException(
            status_code=status_code,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"} if status_code == 401 else None,
        )

def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Validate that the current user is active (Removed check as model lacks field)
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Active user model
        
    Raises:
        HTTPException: If user is inactive (Removed check)
    """
    return current_user

def get_current_active_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Validate that the current user is a superuser/admin
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Admin user model
        
    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_admin:
        logger.warning(f"User {current_user.email} attempted to access superuser endpoint")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges",
        )
    return current_user

def get_current_admin_user(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Validate that the current user is an admin
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Admin user model
        
    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.is_admin:
        logger.warning(f"User {current_user.email} attempted to access admin endpoint")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return current_user

def get_interview_owner_or_admin(
    interview_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> User:
    """
    Validate that the current user is either the interview owner or an admin
    
    Args:
        interview_id: ID of the interview
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        User: Authorized user model
        
    Raises:
        HTTPException: If user is not authorized
    """
    from ..models.interview import Interview
    
    # Get interview
    interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found",
        )
    
    # Check if user is admin or interview owner
    if current_user.is_admin or current_user.id == interview.employee_id:
        return current_user
    
    logger.warning(f"User {current_user.email} attempted to access interview {interview_id} without permission")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized to access this interview",
    ) 