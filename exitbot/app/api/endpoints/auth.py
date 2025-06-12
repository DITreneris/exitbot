"""
Authentication API endpoints for user login and token management
"""
import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ...schemas.user import UserInDB  # Direct import
from ...schemas.token import (
    Token,
    EmployeeAccessToken,
    EmployeeAccessRequest,
)  # Direct import
from ...core import security  # Corrected relative import
from ...core.config import settings  # Corrected relative import
from ...db.database import get_db  # Corrected: Use database.py
from ...db.models import User  # Correct path to db models
from ..deps import get_current_active_user  # Changed to relative import
from ...db import crud  # Added import for crud
from ...core.security import (
    verify_password,
    create_employee_token,
)  # Added import for verify_password and employee token creator

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/login",  # Changed path to match frontend call
    response_model=Token,
    summary="Login and get access token for HR/Admin users",
    description="""
    OAuth2 compatible token login for registered HR/Admin users.
    Requires valid email and password credentials.
    """,
    response_description="Access token for authentication",
    responses={
        200: {"description": "Successful login, token returned"},
        401: {"description": "Incorrect email or password"},
        422: {"description": "Validation error in credentials"},
    },
)
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    OAuth2 compatible token login, get an access token for future requests

    Args:
        form_data: OAuth2 form with username/password
        db: Database session

    Returns:
        Access token
    """
    email = form_data.username
    password = form_data.password

    user = crud.get_user_by_email(db, email=email)

    if (
        not user
        or not user.hashed_password
        or not verify_password(password, user.hashed_password)
    ):
        logger.warning(f"Failed login attempt for HR/Admin email: {email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(
        subject_email=user.email,
        is_admin=user.is_admin,
        expires_delta=access_token_expires,
    )

    logger.info(f"Admin/HR User {user.id} ({user.email}) logged in successfully")
    return {"access_token": access_token, "token_type": "bearer"}


@router.post(
    "/employee-access",
    response_model=EmployeeAccessToken,
    summary="Get access token for an employee to start an interview",
    description="""
    Provides an access token for a departing employee based on their details.
    If the employee doesn't exist in the system, a user record is created.
    This token allows them to access the interview interface.
    """,
    response_description="Access token and employee ID",
    responses={
        200: {"description": "Successful access, token and ID returned"},
        400: {"description": "Invalid input data"},
        500: {"description": "Internal server error during user lookup/creation"},
    },
)
async def get_employee_access_token(
    employee_data: EmployeeAccessRequest, db: Session = Depends(get_db)
) -> EmployeeAccessToken:
    """
    Provides an access token for an employee, creating them if necessary.
    """
    try:
        logger.info(f"Attempting employee access for email: {employee_data.email}")
        # Get or create the employee user record
        employee = crud.get_or_create_employee(db=db, employee_data=employee_data)

        # Generate a specific, potentially short-lived token for the employee
        access_token = create_employee_token(email=employee.email)

        logger.info(f"Employee access token generated for user ID: {employee.id}")
        return EmployeeAccessToken(access_token=access_token, employee_id=employee.id)
    except Exception as e:
        logger.error(
            f"Error generating employee access token for {employee_data.email}: {str(e)}",
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not process employee access request.",
        )


@router.post(
    "/test-token",
    response_model=UserInDB,
    summary="Test access token",
    description="""
    Test access token validity and get current user information.
    Used for testing authentication and verifying token.
    """,
    response_description="Current user information",
    responses={
        200: {"description": "Valid token, user information returned"},
        401: {"description": "Invalid or expired token"},
    },
)
async def test_token(current_user: User = Depends(get_current_active_user)):
    """
    Test access token and get current user

    Args:
        current_user: Current authenticated user from token

    Returns:
        Current user information
    """
    return current_user
