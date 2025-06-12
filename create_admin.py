import sys
import os
from sqlalchemy.orm import Session

# Add project root to sys.path to allow imports from app
project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), ".")
)  # Assumes script is in project root
sys.path.insert(0, project_root)

# --- Imports from your application ---
# Adjust these paths if your structure is different
try:
    from exitbot.app.db.database import (
        db_connection,
    )  # Import the connection manager instance
    from exitbot.app.schemas.user import UserCreate
    from exitbot.app.db.crud.user import create_user, get_user_by_email
    from exitbot.app.core.security import (
        get_password_hash,
    )  # Import for optional password update
except ImportError as e:
    print(f"Error importing application modules: {e}")
    print(
        "Please ensure the script is run from the project root directory and the virtual environment is active."
    )
    sys.exit(1)


# --- Admin User Details ---
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "Password123"  # Changed from "password"
ADMIN_FULL_NAME = "Admin User"
ADMIN_DEPARTMENT = "Administration"


def create_admin_user():
    """Creates the admin user if it doesn't exist."""
    print("Connecting to database...")
    db: Session = db_connection.SessionLocal()  # Get session from the instance
    print("Database session opened.")
    try:
        # Check if user already exists
        print(f"Checking for existing user '{ADMIN_EMAIL}'...")
        user = get_user_by_email(db, email=ADMIN_EMAIL)
        if user:
            print(f"User '{ADMIN_EMAIL}' already exists.")
            # Optional: Add logic here to update the password if needed
            print(f"Ensuring password is correct for user '{ADMIN_EMAIL}'...")
            # Hash the desired password
            hashed_password = get_password_hash(ADMIN_PASSWORD)
            # Check if the stored hash matches the desired one
            if user.hashed_password != hashed_password:
                print("Stored password does not match. Updating...")
                user.hashed_password = hashed_password
                db.commit()
                print(f"Password for user '{ADMIN_EMAIL}' updated successfully.")
            else:
                print("Stored password already matches. No update needed.")
        else:
            # Create the user
            print(f"User '{ADMIN_EMAIL}' not found. Creating...")
            user_in = UserCreate(
                email=ADMIN_EMAIL,
                password=ADMIN_PASSWORD,
                full_name=ADMIN_FULL_NAME,
                is_admin=True,  # Make sure this user is an admin
                department=ADMIN_DEPARTMENT,
            )
            db_user = create_user(db=db, user_in=user_in)
            print(
                f"Admin user '{db_user.email}' created successfully with ID: {db_user.id}."
            )

    except Exception as e:
        print(f"An error occurred during database operation: {e}")
        print("Rolling back transaction...")
        db.rollback()  # Rollback in case of error during creation
    finally:
        print("Closing database session.")
        db.close()


if __name__ == "__main__":
    print("Attempting to create admin user...")
    create_admin_user()
    print("Script finished.")
