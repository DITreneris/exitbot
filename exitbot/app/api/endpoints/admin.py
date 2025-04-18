"""
Admin API endpoints for system configuration and management.
"""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy.orm import Session

from app import models, schemas, crud
from app.api import deps
from app.core.config import settings
from app.core.security import get_password_hash

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get(
    "/users", 
    response_model=List[schemas.User],
    summary="List all users",
    description="""
    Retrieve a list of all users in the system.
    Only accessible to admin users.
    """,
    response_description="List of users",
    responses={
        200: {"description": "Success"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Admin privileges required"}
    }
)
async def list_users(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
    skip: int = Query(0, description="Number of users to skip", ge=0),
    limit: int = Query(100, description="Maximum number of users to return", le=1000),
    is_active: Optional[bool] = Query(None, description="Filter by active status")
) -> List[schemas.User]:
    """
    Get list of all users.
    
    Parameters:
    - skip: Number of users to skip for pagination
    - limit: Maximum number of users to return
    - is_active: Optional filter for active status
    
    Returns:
    - List of User objects
    """
    users = crud.user.get_multi(
        db, skip=skip, limit=limit, filters={"is_active": is_active} if is_active is not None else None
    )
    
    logger.info(f"User list retrieved by admin {current_user.id}")
    return users


@router.post(
    "/users", 
    response_model=schemas.User,
    status_code=status.HTTP_201_CREATED,
    summary="Create new user",
    description="""
    Create a new user with admin-specified attributes.
    Only accessible to admin users.
    """,
    response_description="Created user information",
    responses={
        201: {"description": "User successfully created"},
        400: {"description": "Email already registered"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Admin privileges required"},
        422: {"description": "Validation error in user data"}
    }
)
async def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> schemas.User:
    """
    Create new user as admin.
    
    Parameters:
    - user_in: User creation data
    
    Returns:
    - Created User object
    
    Raises:
    - HTTPException 400: If email already exists
    """
    # Check if user with this email already exists
    existing_user = crud.user.get_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = crud.user.create(db, obj_in=user_in)
    
    logger.info(f"User {user.id} created by admin {current_user.id}")
    return user


@router.get(
    "/users/{user_id}", 
    response_model=schemas.User,
    summary="Get user details",
    description="""
    Retrieve detailed information about a specific user.
    Only accessible to admin users.
    """,
    response_description="User details",
    responses={
        200: {"description": "Success"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Admin privileges required"},
        404: {"description": "User not found"}
    }
)
async def get_user(
    user_id: int = Path(..., description="The ID of the user to get", ge=1),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> schemas.User:
    """
    Get detailed information about a specific user.
    
    Parameters:
    - user_id: ID of the user to retrieve
    
    Returns:
    - User object
    
    Raises:
    - HTTPException 404: If user not found
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.put(
    "/users/{user_id}", 
    response_model=schemas.User,
    summary="Update user",
    description="""
    Update attributes of a specific user.
    Only accessible to admin users.
    """,
    response_description="Updated user information",
    responses={
        200: {"description": "User successfully updated"},
        400: {"description": "Email already registered to another user"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Admin privileges required"},
        404: {"description": "User not found"},
        422: {"description": "Validation error in update data"}
    }
)
async def update_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int = Path(..., description="The ID of the user to update", ge=1),
    user_in: schemas.UserUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> schemas.User:
    """
    Update a user.
    
    Parameters:
    - user_id: ID of the user to update
    - user_in: User update data
    
    Returns:
    - Updated User object
    
    Raises:
    - HTTPException 404: If user not found
    - HTTPException 400: If email already exists for another user
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if updating email to one that already exists
    if user_in.email and user_in.email != user.email:
        existing_user = crud.user.get_by_email(db, email=user_in.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered to another user"
            )
    
    # Update user
    updated_user = crud.user.update(db, db_obj=user, obj_in=user_in)
    
    logger.info(f"User {user_id} updated by admin {current_user.id}")
    return updated_user


@router.delete(
    "/users/{user_id}", 
    response_model=schemas.User,
    summary="Delete user",
    description="""
    Delete a specific user from the system.
    Only accessible to admin users.
    """,
    response_description="Deleted user information",
    responses={
        200: {"description": "User successfully deleted"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Admin privileges required or attempt to delete self"},
        404: {"description": "User not found"}
    }
)
async def delete_user(
    user_id: int = Path(..., description="The ID of the user to delete", ge=1),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> schemas.User:
    """
    Delete a user.
    
    Parameters:
    - user_id: ID of the user to delete
    
    Returns:
    - Deleted User object
    
    Raises:
    - HTTPException 404: If user not found
    - HTTPException 403: If attempting to delete self
    """
    # Prevent admin from deleting themselves
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete your own user account"
        )
    
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Delete user
    user = crud.user.remove(db, id=user_id)
    
    logger.info(f"User {user_id} deleted by admin {current_user.id}")
    return user


@router.post(
    "/system/reset-password/{user_id}", 
    response_model=schemas.Message,
    summary="Reset user password",
    description="""
    Reset a user's password to a new admin-specified password.
    Only accessible to admin users.
    """,
    response_description="Success message",
    responses={
        200: {"description": "Password successfully reset"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Admin privileges required"},
        404: {"description": "User not found"},
        422: {"description": "Validation error in password data"}
    }
)
async def reset_password(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int = Path(..., description="The ID of the user", ge=1),
    password_data: schemas.PasswordReset,
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> schemas.Message:
    """
    Reset a user's password.
    
    Parameters:
    - user_id: ID of the user
    - password_data: New password data
    
    Returns:
    - Success message
    
    Raises:
    - HTTPException 404: If user not found
    """
    user = crud.user.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    hashed_password = get_password_hash(password_data.new_password)
    user.hashed_password = hashed_password
    db.add(user)
    db.commit()
    
    logger.info(f"Password reset for user {user_id} by admin {current_user.id}")
    return {"message": f"Password for user {user.email} reset successfully"}


@router.get(
    "/system/config", 
    response_model=Dict[str, Any],
    summary="Get system configuration",
    description="""
    Retrieve current system configuration settings.
    Only accessible to admin users.
    """,
    response_description="System configuration",
    responses={
        200: {"description": "Success"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Admin privileges required"}
    }
)
async def get_system_config(
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> Dict[str, Any]:
    """
    Get system configuration settings.
    
    Returns:
    - Dictionary of configuration settings
    """
    # Return a subset of settings that are safe to expose
    safe_settings = {
        "project_name": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0",  # This could be dynamically determined
        "api_prefix": settings.API_V1_PREFIX,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.GROQ_MODEL if settings.LLM_PROVIDER == "groq" else settings.OLLAMA_MODEL,
        "access_token_expire_minutes": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        "cors_origins": settings.BACKEND_CORS_ORIGINS
    }
    
    logger.info(f"System configuration retrieved by admin {current_user.id}")
    return safe_settings


@router.post(
    "/interviews/bulk-update-status", 
    response_model=schemas.BulkUpdateResponse,
    summary="Bulk update interview status",
    description="""
    Update the status of multiple interviews at once.
    Only accessible to admin users.
    """,
    response_description="Bulk update result",
    responses={
        200: {"description": "Interviews successfully updated"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Admin privileges required"},
        422: {"description": "Validation error in update data"}
    }
)
async def bulk_update_interview_status(
    *,
    db: Session = Depends(deps.get_db),
    update_data: schemas.BulkInterviewStatusUpdate,
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> schemas.BulkUpdateResponse:
    """
    Bulk update the status of multiple interviews.
    
    Parameters:
    - update_data: Bulk update data containing interview IDs and new status
    
    Returns:
    - BulkUpdateResponse with success count and failures
    """
    # Track success and failures
    success_count = 0
    failures = []
    
    for interview_id in update_data.interview_ids:
        try:
            interview = crud.interview.get(db, id=interview_id)
            if not interview:
                failures.append({
                    "id": interview_id,
                    "error": "Interview not found"
                })
                continue
            
            # Update interview status
            crud.interview.update(
                db, 
                db_obj=interview, 
                obj_in={"status": update_data.new_status}
            )
            success_count += 1
            
        except Exception as e:
            failures.append({
                "id": interview_id,
                "error": str(e)
            })
    
    logger.info(
        f"Bulk status update to '{update_data.new_status}' for {success_count} interviews "
        f"by admin {current_user.id}"
    )
    return {
        "success_count": success_count,
        "failure_count": len(failures),
        "failures": failures
    }


@router.get(
    "/system/logs", 
    response_model=List[Dict[str, Any]],
    summary="Get system logs",
    description="""
    Retrieve recent system logs for monitoring.
    Only accessible to admin users.
    """,
    response_description="System logs",
    responses={
        200: {"description": "Success"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Admin privileges required"}
    }
)
async def get_system_logs(
    current_user: models.User = Depends(deps.get_current_active_superuser),
    limit: int = Query(100, description="Maximum number of log entries to return", le=1000),
    level: Optional[str] = Query(None, description="Filter by log level (info, warning, error)"),
    component: Optional[str] = Query(None, description="Filter by component name")
) -> List[Dict[str, Any]]:
    """
    Get recent system logs.
    
    Parameters:
    - limit: Maximum number of log entries to return
    - level: Optional filter by log level
    - component: Optional filter by component
    
    Returns:
    - List of log entries
    """
    # Implementation note: This is a placeholder.
    # In a real application, you would retrieve logs from a database or log files.
    # For demonstration purposes, we return a static response.
    
    logger.info(f"System logs retrieved by admin {current_user.id}")
    
    # Example response (would be replaced with actual log retrieval)
    return [
        {
            "timestamp": "2023-06-01T12:00:00Z",
            "level": "INFO",
            "component": "auth",
            "message": "User logged in successfully",
            "details": {"user_id": 123}
        },
        {
            "timestamp": "2023-06-01T12:01:00Z",
            "level": "WARNING",
            "component": "interview",
            "message": "Interview session timeout",
            "details": {"interview_id": 456}
        }
    ][:limit] 