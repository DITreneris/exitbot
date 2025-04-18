"""
Token schemas for API authentication
"""
from typing import Optional
from pydantic import BaseModel

class Token(BaseModel):
    """OAuth2 compatible token schema"""
    access_token: str
    token_type: str = "bearer"
    
class TokenPayload(BaseModel):
    """JWT token payload schema"""
    sub: Optional[str] = None
    exp: Optional[int] = None
    is_admin: bool = False 