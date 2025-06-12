"""
Pydantic models for user data.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


class UserBase(BaseModel):
    """Base schema with common user attributes."""

    email: EmailStr = Field(..., description="User's email address (must be unique)")
    full_name: str = Field(..., description="User's full name", min_length=2)
    department: Optional[str] = Field(None, description="User's department")
    position: Optional[str] = Field(None, description="User's job position")
    is_admin: bool = Field(
        default=False, description="Whether the user has admin privileges"
    )


class UserCreate(UserBase):
    """Schema for creating a new user."""

    password: str = Field(..., description="User's password", min_length=8)

    @field_validator("password")
    def validate_password_strength(cls, v):
        """Validate that the password meets strength requirements."""
        # At least 8 characters
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        # Check for at least one uppercase letter
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")

        # Check for at least one digit
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")

        return v


class UserUpdate(BaseModel):
    """Schema for updating an existing user."""

    email: Optional[EmailStr] = Field(None, description="User's email address")
    full_name: Optional[str] = Field(None, description="User's full name", min_length=2)
    password: Optional[str] = Field(None, description="User's password", min_length=8)
    department: Optional[str] = Field(None, description="User's department")
    position: Optional[str] = Field(None, description="User's job position")
    is_admin: Optional[bool] = Field(
        None, description="Whether the user has admin privileges"
    )

    @field_validator("password")
    def validate_password_strength(cls, v):
        """Validate that the password meets strength requirements."""
        if v is None:
            return v

        # At least 8 characters
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        # Check for at least one uppercase letter
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")

        # Check for at least one digit
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")

        return v


class UserInDB(UserBase):
    """Schema for user data as stored in the database."""

    id: int = Field(..., description="Unique user ID")
    created_at: datetime = Field(..., description="When the user account was created")
    updated_at: Optional[datetime] = Field(
        None, description="When the user account was last updated"
    )
    last_login: Optional[datetime] = Field(
        None, description="When the user last logged in"
    )

    model_config = {"from_attributes": True}


class User(UserInDB):
    """Schema for user data to be returned via API."""

    pass


class UserList(BaseModel):
    """Schema for a list of users."""

    total: int = Field(..., description="Total number of users")
    items: List[User] = Field(..., description="List of users")


class ChangePassword(BaseModel):
    """Schema for changing a user's password."""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., description="New password", min_length=8)

    @field_validator("new_password")
    def validate_password_strength(cls, v):
        """Validate that the password meets strength requirements."""
        # At least 8 characters
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")

        # Check for at least one uppercase letter
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain at least one uppercase letter")

        # Check for at least one digit
        if not re.search(r"\d", v):
            raise ValueError("Password must contain at least one digit")

        return v


class UserProfile(BaseModel):
    """Schema for user profile data."""

    id: int = Field(..., description="Unique user ID")
    email: EmailStr = Field(..., description="User's email address")
    full_name: str = Field(..., description="User's full name")
    department: Optional[str] = Field(None, description="User's department")
    position: Optional[str] = Field(None, description="User's job position")
    avatar_url: Optional[str] = Field(None, description="URL to user's avatar image")
    bio: Optional[str] = Field(None, description="User's biographical information")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metadata about the user"
    )

    model_config = {"from_attributes": True}


class ProfileUpdate(BaseModel):
    """Schema for updating user profile data."""

    full_name: Optional[str] = Field(None, description="User's full name", min_length=2)
    department: Optional[str] = Field(None, description="User's department")
    position: Optional[str] = Field(None, description="User's job position")
    bio: Optional[str] = Field(None, description="User's biographical information")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata about the user"
    )
