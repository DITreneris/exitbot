from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

# Import password hashing from core security module
# Only import if actually needed for creating users with passwords
from exitbot.app.core.security import get_password_hash

from exitbot.app.db.models import User
from exitbot.app.schemas.user import UserCreate
from exitbot.app.schemas.token import EmployeeAccessRequest  # Import the new schema
from fastapi import HTTPException, status  # Import HTTPException


# User operations
def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user_in: UserCreate) -> User:
    # Hash the password before creating the user
    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        full_name=user_in.full_name,
        is_admin=user_in.is_admin,
        department=user_in.department,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_last_login(db: Session, user_id: int) -> Optional[User]:
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db_user.last_login = datetime.utcnow()
        db.commit()
        db.refresh(db_user)
    return db_user


# Add get_user_by_username if it doesn't exist
def get_user_by_username(db: Session, username: str) -> Optional[User]:
    # Assuming username is email for login purposes
    return db.query(User).filter(User.email == username).first()


def get_or_create_employee(db: Session, employee_data: EmployeeAccessRequest) -> User:
    """Gets an employee by email, creating if non-existent, or verifies full name if existing."""
    db_user = get_user_by_email(db, email=employee_data.email)
    if db_user:
        # User exists, verify provided full name matches existing record
        details_match = True
        mismatch_reason = ""

        # Compare full_name (case-sensitive for now)
        if employee_data.full_name != db_user.full_name:
            details_match = False
            mismatch_reason = "Full name does not match existing record."

        # Removed department check
        # if employee_data.department is not None and employee_data.department != db_user.department:
        #      # Also check if db_user.department is None - allow matching None to None implicitly
        #      if db_user.department is not None or employee_data.department is not None:
        #         details_match = False
        #         mismatch_reason = "Department does not match existing record."

        if not details_match:
            # Log the attempt? Depends on security policy
            # logger.warning(f"Employee access attempt failed for email {employee_data.email}: {mismatch_reason}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,  # Or 403 Forbidden?
                detail=f"Provided full name does not match the record associated with this email. {mismatch_reason}",
            )
        # Details match, return existing user
        return db_user
    else:
        # Create a new user (employee)
        # Note: No password is set here, hashed_password will be NULL
        new_employee = User(
            email=employee_data.email,
            full_name=employee_data.full_name,
            # department=employee_data.department, # Removed department
            is_admin=False,  # Employees are not admins by default
        )
        db.add(new_employee)
        db.commit()
        db.refresh(new_employee)
        return new_employee
