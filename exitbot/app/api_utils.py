from typing import Any, Dict, Optional, Union, List
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime

class APIResponse(BaseModel):
    """Standard API response model"""
    status: str
    message: str
    data: Optional[Union[Dict[str, Any], List[Any]]] = None
    timestamp: str = datetime.now().isoformat()

class APIError(BaseModel):
    """Standard API error model"""
    status: str = "error"
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    timestamp: str = datetime.now().isoformat()

def success_response(
    message: str = "Operation successful",
    data: Optional[Union[Dict[str, Any], List[Any]]] = None
) -> JSONResponse:
    """Create a standardized success response"""
    response = APIResponse(
        status="success",
        message=message,
        data=data
    )
    return JSONResponse(content=response.model_dump())

def error_response(
    message: str,
    status_code: int = 400,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create a standardized error response"""
    error = APIError(
        message=message,
        error_code=error_code,
        details=details
    )
    return JSONResponse(
        status_code=status_code,
        content=error.model_dump()
    )

class APIException(HTTPException):
    """Custom API exception with standardized error format"""
    def __init__(
        self,
        message: str,
        status_code: int = 400,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        error_content = APIError(
            message=message,
            error_code=error_code,
            details=details
        ).model_dump()
        
        super().__init__(
            status_code=status_code,
            detail=error_content
        ) 