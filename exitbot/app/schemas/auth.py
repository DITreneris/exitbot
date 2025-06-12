from typing import Optional
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    department: Optional[str] = None
    is_admin: bool = False


class UserCreate(UserBase):
    password: Optional[str] = None


class User(UserBase):
    id: int

    model_config = {"from_attributes": True}


class UserInDB(User):
    hashed_password: Optional[str] = None


class Token(BaseModel):
    """Schema for authentication token"""

    access_token: str
    token_type: str


class TokenData(BaseModel):
    """Schema for token data"""

    email: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class EmployeeAccessRequest(BaseModel):
    email: EmailStr
    full_name: str
    department: Optional[str] = None
    exit_date: Optional[str] = None
