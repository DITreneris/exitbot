"""
Pytest configuration file for ExitBot application
"""
import os
import sys
import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session
import time
from fastapi import FastAPI

# Add app directory to path - this needs to be BEFORE any exitbot imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

# Now import exitbot modules using the correct paths
from exitbot.app.core.config import settings
from exitbot.app.db.base import Base
from exitbot.app.db.database import get_db
# Restore import of global app
from exitbot.app.main import app 
# Removed: from exitbot.app.api.api import api_router 
# Split imports for models and schemas
from exitbot.app.db.models import User 
from exitbot.app.schemas.user import UserCreate
from exitbot.app.core.security import create_access_token, get_password_hash
from exitbot.tests.mocks import setup_mock_ollama, teardown_mock_ollama
import exitbot.app.db.models # noqa F401: Ensure models are registered with Base metadata
# Import necessary endpoint routers
from exitbot.app.api.endpoints import auth as auth_router
from exitbot.app.api.endpoints import interviews as interviews_router
# ADDED: Import the dependency function to override
from exitbot.app.api.deps import get_current_active_user

@pytest.fixture(scope="function") # Scope changed to function
def test_db():
    """Test database session fixture using in-memory SQLite."""
    # Define engine and sessionmaker inside the function scope
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}, # Needed for SQLite
        poolclass=StaticPool, # Important for in-memory SQLite testing
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create tables using the function-scoped engine
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop tables using the function-scoped engine
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function") 
def client(test_db: Session): 
    """Create test client using the global app and overriding DB dependency."""
    
    # Define the override function here
    def override_get_db():
        # This yields the function-scoped test_db session
        try:
            yield test_db
        finally:
            pass # test_db fixture handles closing

    # Apply the override to the global app *before* TestClient init
    app.dependency_overrides[get_db] = override_get_db 
    print("DEBUG [conftest]: Applied DB override to global app")

    # Initialize TestClient with the global app instance
    with TestClient(app, raise_server_exceptions=False) as c:
        print("DEBUG [conftest]: Initialized TestClient with global_app")
        yield c 
    
    # Clean up the override after the test completes
    app.dependency_overrides.pop(get_db, None)
    print("DEBUG [conftest]: Cleared DB override from global app")

@pytest.fixture(scope="function") # Scope changed
def test_admin(test_db: Session) -> User: # Use test_db session, removed client dependency
    """Create a test admin user."""
    from exitbot.app.db.crud import create_user
    # Use a unique email for each function scope
    email = f"admin_{datetime.now().timestamp()}@example.com"
    user_data = {
        "email": email,
        "password": "AdminPassword1", # Ensure password meets requirements
        "full_name": "Test Admin",
        "is_admin": True,
        "department": "IT"
    }
    user = create_user(db=test_db, user_data=user_data)
    return user # Return the actual DB object

@pytest.fixture(scope="function") # Scope changed
def test_hr(test_db: Session) -> User: # Use test_db session, removed client dependency
    """Create a test HR user."""
    from exitbot.app.db.crud import create_user
    email = f"hr_{datetime.now().timestamp()}@example.com"
    user_data = {
        "email": email,
        "password": "HrPassword1", # Ensure password meets requirements
        "full_name": "Test HR",
        "is_admin": True, # Assuming HR maps to is_admin=True
        "department": "HR"
    }
    user = create_user(db=test_db, user_data=user_data)
    return user

@pytest.fixture(scope="function") # Scope changed
def test_employee(test_db: Session) -> User: # Use test_db session, removed client dependency
    """Create a test employee user."""
    from exitbot.app.db.crud import create_user
    email = f"employee_{datetime.now().timestamp()}@example.com"
    user_data = {
        "email": email,
        "password": "EmpPassword1", # Ensure password meets requirements
        "full_name": "Test Employee",
        "is_admin": False,
        "department": "Sales"
    }
    user = create_user(db=test_db, user_data=user_data)
    return user

@pytest.fixture(scope="function") # Scope changed
def admin_token(test_admin: User):
    """Create admin access token using user email as subject"""
    return create_access_token(subject_email=test_admin.email, is_admin=True)

@pytest.fixture(scope="function") # Scope changed
def hr_token(test_hr: User):
    """Create HR access token using user email as subject"""
    return create_access_token(subject_email=test_hr.email, is_admin=True)

@pytest.fixture(scope="function") # Scope changed
def employee_token(test_employee: User):
    """Create employee access token using user email as subject"""
    return create_access_token(subject_email=test_employee.email, is_admin=False)

@pytest.fixture
def expired_token():
    """Expired JWT token for testing"""
    return create_access_token(
        subject_email="expireduser@example.com",
        expires_delta=timedelta(minutes=-10)  # Already expired
    )

@pytest.fixture(scope="function") # Scope changed
def mock_auth_user(test_employee: User): # Depends on function-scoped test_employee
    """Mock authenticated user for auth-requiring endpoints"""
    # Verify this patch path: exitbot.app.api.deps.get_current_user
    with patch("exitbot.app.api.deps.get_current_user") as mock_get_current_user:
        mock_get_current_user.return_value = test_employee
        yield test_employee

@pytest.fixture(scope="function") # Scope changed
def mock_auth_admin(test_admin: User): # Depends on function-scoped test_admin
    """Mock authenticated admin for admin-requiring endpoints"""
    # Verify this patch path: exitbot.app.api.deps.get_current_user
    with patch("exitbot.app.api.deps.get_current_user") as mock_get_current_user:
        mock_get_current_user.return_value = test_admin
        yield test_admin

def pytest_configure(config):
    """Configure pytest with coverage settings"""
    config.option.cov_branch = True
    config.option.cov_report = {
        'html': 'test_reports/coverage',
        'xml': 'test_reports/coverage.xml',
        'term-missing': True
    }
    
    # Create reports directory if it doesn't exist
    os.makedirs('test_reports', exist_ok=True)

@pytest.fixture
def event_loop():
    """Custom event loop for asyncio tests"""
    import asyncio
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()

# Define base test user data
test_user_data = {
    "email_base": "testuser",
    "password": "SecurePassword123!",
    "full_name": "Test User",
    "domain": "example.com"
}

test_admin_data = {
    "email_base": "testadmin",
    "password": "SecureAdminPassword123!",
    "full_name": "Admin User",
    "domain": "example.com"
}

# Helper function to create unique emails
def create_unique_email(base, domain):
    timestamp = int(time.time() * 1000) # Milliseconds for higher uniqueness
    return f"{base}_{timestamp}@{domain}"

# Fixture to create a regular user in the test DB
@pytest.fixture(scope="function")
def test_user(test_db):
    """Creates a regular user in the test database for function scope."""
    unique_email = create_unique_email(test_user_data["email_base"], test_user_data["domain"])
    user = User(
        email=unique_email,
        hashed_password=get_password_hash(test_user_data["password"]),
        full_name=test_user_data["full_name"],
        is_admin=False
    )
    test_db.add(user)
    test_db.commit()
    test_db.refresh(user)
    return user # Return the actual User object

# Fixture to create an admin user in the test DB
@pytest.fixture(scope="function")
def test_admin_user(test_db):
    """Creates an admin user in the test database for function scope."""
    unique_email = create_unique_email(test_admin_data["email_base"], test_admin_data["domain"])
    admin = User(
        email=unique_email,
        hashed_password=get_password_hash(test_admin_data["password"]),
        full_name=test_admin_data["full_name"],
        is_admin=True # Set admin flag
    )
    test_db.add(admin)
    test_db.commit()
    test_db.refresh(admin)
    return admin # Return the actual User object

# Fixture to generate a token for the regular test user
@pytest.fixture(scope="function")
def test_token(test_user):
    """Generates an access token for the function-scoped test_user."""
    # Use the email from the actual user created by the test_user fixture
    return create_access_token(subject_email=test_user.email, is_admin=test_user.is_admin)

# Fixture to generate a token for the admin test user
@pytest.fixture(scope="function")
def admin_token_user(test_admin_user):
    """Generates an access token for the function-scoped test_admin_user."""
    # Use the email from the actual user created by the test_admin_user fixture
    return create_access_token(subject_email=test_admin_user.email, is_admin=test_admin_user.is_admin)

# If some tests still need a purely mocked DB session, you can keep this,
# but prefer using the real test_db where possible.
# @pytest.fixture
# def mock_db_session():
#     """Provides a MagicMock for the database session."""
#     session = MagicMock(spec=Session)
#     session.query.return_value.filter.return_value.first.return_value = None # Default mock behavior
#     session.add = MagicMock()
#     session.commit = MagicMock()
#     session.refresh = MagicMock()
#     return session

# # Override get_db with the mock session if needed for specific tests
# @pytest.fixture
# def mock_client(mock_db_session):
#     """Provides a TestClient with the database dependency overridden by a mock."""
#     def override_get_db_mock():
#         yield mock_db_session

#     app.dependency_overrides[get_db] = override_get_db_mock
#     with TestClient(app) as c:
#         yield c
#     # Clean up
#     app.dependency_overrides.pop(get_db, None) 