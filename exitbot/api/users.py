from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field

from exitbot.database.crud import (
    get_user_by_email,
    get_user_by_id,
    get_users,
    create_user,
    update_user,
    delete_user,
    verify_password,
)
from exitbot.database.database import get_db
from exitbot.database.models import User
from exitbot.api.auth import (
    get_current_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)

router = APIRouter(prefix="/api/users", tags=["users"])


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str
    department: Optional[str] = None
    is_hr: bool = False
    is_admin: bool = False


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    department: Optional[str] = None
    is_hr: Optional[bool] = None
    is_admin: Optional[bool] = None


class Token(BaseModel):
    access_token: str
    token_type: str
    user_info: dict


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    department: Optional[str]
    is_hr: bool
    is_admin: bool
    created_at: datetime


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    Authenticate user and provide access token
    """
    user = get_user_by_email(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    # Return token and user info
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_info": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "is_hr": user.is_hr,
            "is_admin": user.is_admin,
            "department": user.department,
        },
    }


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Register a new user (admin only)
    """
    # Only admins can create new users
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403, detail="Only administrators can register new users"
        )

    # Check if user with this email already exists
    db_user = get_user_by_email(db, user_data.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create the new user
    new_user = create_user(db, user_data)

    return new_user


@router.get("/me", response_model=UserResponse)
async def read_current_user(current_user: User = Depends(get_current_user)):
    """
    Get information about the current logged-in user
    """
    return current_user


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List all users (admin only)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403, detail="Only administrators can view all users"
        )

    users = get_users(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int = Path(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Get a specific user by ID (admin only)
    """
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this user's information"
        )

    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user_info(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update user info (admin/owner)
    """
    # Check permissions
    if not current_user.is_admin and current_user.id != user_id:
        raise HTTPException(
            status_code=403, detail="Not authorized to update this user"
        )

    # If not admin, restrict fields that can be updated
    if not current_user.is_admin and current_user.id == user_id:
        # Regular users can only update their name and department
        if user_update.is_hr is not None or user_update.is_admin is not None:
            raise HTTPException(
                status_code=403, detail="You cannot modify permission fields"
            )

    # Update the user
    updated_user = update_user(db, user_id, user_update)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    return updated_user


@router.delete("/{user_id}")
async def remove_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Delete a user (admin only)
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=403, detail="Only administrators can delete users"
        )

    # Prevent admins from deleting themselves
    if current_user.id == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")

    # Delete the user
    success = delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    return {"status": "success", "message": f"User {user_id} deleted successfully"}
