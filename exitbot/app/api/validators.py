"""
Input validation utilities for API endpoints
"""
import logging
import re
from typing import Any, Dict, Optional, Type, TypeVar, Union, List

from fastapi import HTTPException, status
from pydantic import BaseModel, ValidationError

# Configure logger
logger = logging.getLogger(__name__)

# Generic type for Pydantic models
T = TypeVar('T', bound=BaseModel)

def validate_model_input(model_class: Type[T], data: Dict[str, Any]) -> T:
    """
    Validate input data against Pydantic model with enhanced error handling
    
    Args:
        model_class: Pydantic model class to validate against
        data: Input data to validate
        
    Returns:
        Instance of validated model
        
    Raises:
        HTTPException: If validation fails
    """
    try:
        # Validate with Pydantic model
        return model_class(**data)
    except ValidationError as e:
        # Extract validation errors
        error_details = []
        for error in e.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            message = error["msg"]
            error_details.append(f"{field}: {message}")
        
        # Log validation error
        logger.warning(f"Validation error: {'; '.join(error_details)}")
        
        # Raise HTTP exception
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Validation error",
                "errors": error_details
            }
        )
    except Exception as e:
        # Log unexpected error
        logger.error(f"Unexpected error during validation: {str(e)}")
        
        # Raise HTTP exception
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid input: {str(e)}"
        )

def sanitize_html(text: str) -> str:
    """
    Sanitize HTML to prevent XSS attacks
    
    Args:
        text: Input text that may contain HTML
        
    Returns:
        Sanitized text with HTML tags removed
    """
    if not text:
        return ""
    
    # Remove HTML tags
    sanitized = re.sub(r'<[^>]*>', '', text)
    
    # Replace potentially dangerous characters
    sanitized = sanitized.replace('&', '&amp;')
    sanitized = sanitized.replace('<', '&lt;')
    sanitized = sanitized.replace('>', '&gt;')
    sanitized = sanitized.replace('"', '&quot;')
    sanitized = sanitized.replace("'", '&#x27;')
    
    return sanitized

def validate_entity_exists(entity: Optional[Any], entity_name: str, entity_id: Union[int, str]) -> Any:
    """
    Validate that an entity exists
    
    Args:
        entity: Entity to validate
        entity_name: Name of entity for error messages
        entity_id: ID of entity for error messages
        
    Returns:
        Entity if it exists
        
    Raises:
        HTTPException: If entity does not exist
    """
    if not entity:
        logger.warning(f"{entity_name} with ID {entity_id} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{entity_name} not found"
        )
    return entity

def validate_permission(has_permission: bool, message: str = "Permission denied") -> None:
    """
    Validate that user has permission
    
    Args:
        has_permission: Whether user has permission
        message: Error message if permission check fails
        
    Raises:
        HTTPException: If user does not have permission
    """
    if not has_permission:
        logger.warning(f"Permission check failed: {message}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=message
        )

def sanitize_model_inputs(model: BaseModel) -> BaseModel:
    """
    Sanitize all string fields in a Pydantic model
    
    Args:
        model: Pydantic model to sanitize
        
    Returns:
        Sanitized model
    """
    data = model.dict()
    for field, value in data.items():
        if isinstance(value, str):
            data[field] = sanitize_html(value)
        elif isinstance(value, list) and all(isinstance(item, str) for item in value):
            data[field] = [sanitize_html(item) for item in value]
    
    return model.__class__(**data) 