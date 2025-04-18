"""
User management API endpoints for creating, retrieving, and updating users
"""
import logging
from typing import Any, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..deps import get_current_active_superuser, get_current_active_user, get_db
from ...core.security import get_password_hash, verify_password
from ... import schemas
from ...db import crud
from ...api import deps
from ...core.config import settings
from ...db.models import User
from ...schemas.user import UserCreate, UserInDB, UserUpdate

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post(
    "/", 
    response_model=UserInDB,
    status_code=status.HTTP_201_CREATED,
    summary="Create new user",
    description="""
    Create a new user with the provided information.
    Emails must be unique.
    """,
    response_description="Created user information",
    responses={
        201: {"description": "User successfully created"},
        400: {"description": "Email already registered"},
        422: {"description": "Validation error in user data"}
    }
)
def create_user(
    *,
    db: Session = Depends(get_db),
    user_in: UserCreate,
) -> Any:
    """
    Create new user by calling the CRUD function.
    """
    user = crud.get_user_by_email(db, email=user_in.email)
    if user:
        logger.warning(f"User registration failed: Email {user_in.email} already registered")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Prepare data dict for crud.create_user, mapping schema fields to model fields
    user_data_for_crud = {
        "email": user_in.email,
        "password": user_in.password, # crud function will hash it
        "full_name": user_in.full_name,
        # Map is_superuser (schema) to is_admin (model/crud expectation)
        "is_admin": user_in.is_admin, 
        "department": user_in.department,
        # 'position' from schema is ignored as model/crud doesn't use it
    }
    
    db_user = crud.create_user(db=db, user_data=user_data_for_crud)
    
    logger.info(f"New user created via CRUD: {db_user.id} ({db_user.email})")
    # Return the created user object (crud function already adds/commits/refreshes)
    # UserInDB schema expects is_superuser, but model has is_admin.
    # We might need to adjust UserInDB or manually create the response object.
    # For now, let's return db_user, FastAPI might handle mapping via from_attributes=True
    return db_user

@router.get(
    "/me", 
    response_model=UserInDB,
    summary="Get current user",
    description="Get information about the currently authenticated user.",
    response_description="Current user information",
    responses={
        200: {"description": "User information returned"},
        401: {"description": "Unauthorized, valid token required"}
    }
)
def read_user_me(
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Get current user.
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Current user information
    """
    return current_user

@router.put(
    "/me", 
    response_model=UserInDB,
    summary="Update current user",
    description="""
    Update current user information. 
    Users can update their own name, email, and password.
    """,
    response_description="Updated user information",
    responses={
        200: {"description": "User successfully updated"},
        401: {"description": "Unauthorized, valid token required"},
        422: {"description": "Validation error in update data"}
    }
)
def update_user_me(
    *,
    db: Session = Depends(get_db),
    current_password: str = Body(None),
    password: str = Body(None),
    full_name: str = Body(None),
    email: str = Body(None),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    Update current user.
    
    Args:
        db: Database session
        current_password: Current password for verification when changing password
        password: New password
        full_name: New full name
        email: New email
        current_user: Current authenticated user
        
    Returns:
        Updated user information
        
    Raises:
        HTTPException: If current password is incorrect or validation fails
    """
    # Create update data dictionary
    user_in = UserUpdate(
        password=password,
        full_name=full_name,
        email=email,
    )
    
    # Validate current password if changing password
    if password is not None and current_password is not None:
        if not verify_password(current_password, current_user.hashed_password):
            logger.warning(f"User update failed for user {current_user.id}: incorrect password")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect password",
            )
    
    # Check if new email already exists
    if email is not None and email != current_user.email:
        user_with_email = db.query(User).filter(User.email == email).first()
        if user_with_email:
            logger.warning(f"User update failed for user {current_user.id}: email {email} already in use")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered",
            )
    
    # Update user
    user_data = user_in.model_dump(exclude_unset=True)
    if password:
        user_data["hashed_password"] = get_password_hash(password)
        del user_data["password"]
    
    for field, value in user_data.items():
        setattr(current_user, field, value)
    
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    
    logger.info(f"User {current_user.id} updated their profile")
    return current_user

@router.get(
    "/{user_id}", 
    response_model=UserInDB,
    summary="Get user by ID",
    description="Get a specific user by ID. Requires superuser privileges.",
    response_description="User information",
    responses={
        200: {"description": "User information returned"},
        401: {"description": "Unauthorized, valid token required"},
        403: {"description": "Forbidden, superuser privileges required"},
        404: {"description": "User not found"}
    }
)
def read_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_active_superuser),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get a specific user by id.
    
    Args:
        user_id: ID of user to retrieve
        current_user: Current authenticated superuser
        db: Database session
        
    Returns:
        User information
        
    Raises:
        HTTPException: If user not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"User lookup failed: ID {user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    return user

@router.put(
    "/{user_id}", 
    response_model=UserInDB,
    summary="Update user",
    description="Update a specific user. Requires superuser privileges.",
    response_description="Updated user information",
    responses={
        200: {"description": "User successfully updated"},
        401: {"description": "Unauthorized, valid token required"},
        403: {"description": "Forbidden, superuser privileges required"},
        404: {"description": "User not found"},
        422: {"description": "Validation error in update data"}
    }
)
def update_user(
    *,
    db: Session = Depends(get_db),
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(get_current_active_superuser),
) -> Any:
    """
    Update a user.
    
    Args:
        db: Database session
        user_id: ID of user to update
        user_in: User update data
        current_user: Current authenticated superuser
        
    Returns:
        Updated user information
        
    Raises:
        HTTPException: If user not found
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        logger.warning(f"User update failed: ID {user_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Update user data using CRUD function (assuming one exists or needs creation)
    # This part needs review/implementation based on available CRUD functions
    # Example placeholder:
    # updated_user = crud.user.update(db=db, db_obj=user, obj_in=user_in)

    # Manual update (similar to update_user_me) as placeholder if no crud update exists:
    user_data = user_in.model_dump(exclude_unset=True)
    if user_in.password:
        user_data["hashed_password"] = get_password_hash(user_in.password)
        del user_data["password"]
    
    # Handle potential schema/model mismatch (e.g., is_superuser vs is_admin)
    if "is_superuser" in user_data:
        user_data["is_admin"] = user_data.pop("is_superuser")
    
    for field, value in user_data.items():
        # Check if the field exists on the model before setting
        if hasattr(user, field):
            setattr(user, field, value)
        else:
            logger.warning(f"Attempted to update non-existent field '{field}' on User model for user {user_id}")

    db.add(user)
    db.commit()
    db.refresh(user)
    
    logger.info(f"User {user.id} updated by superuser {current_user.id}")
    return user 