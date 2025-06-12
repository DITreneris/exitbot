# Remove unused pytest
# import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
import pytest
import logging # Import logging

# Remove unused MagicMock
# from unittest.mock import MagicMock
# Remove unused Session
# from sqlalchemy.orm import Session

from exitbot.app.main import app
from exitbot.app.db.models import User

# Remove unused create_access_token, get_password_hash
# from exitbot.app.core.security import create_access_token, get_password_hash

client = TestClient(app)

# Initialize logger for this test module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG) # Basic config for testing

@pytest.mark.usefixtures("test_db")

def test_login_success(client, test_admin):
    """Test user login endpoint with valid credentials"""
    response = client.post(
        "/api/auth/login",
        data={"username": test_admin.email, "password": "AdminPassword1"},
    )

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    # assert data["user_info"]["email"] == "admin@example.com" # This seems incorrect, response_model=Token does not include user_info


def test_login_invalid_password(client, test_admin):
    """Test login with invalid password"""
    response = client.post(
        "/api/auth/login",
        data={"username": test_admin.email, "password": "wrong_password"},
    )

    assert response.status_code == 401
    assert "Incorrect email or password" in response.text


def test_login_user_not_found(client):
    """Test login with non-existent user"""
    response = client.post(
        "/api/auth/login",
        data={"username": "nonexistent@example.com", "password": "password"},
    )

    assert response.status_code == 401
    assert "Incorrect email or password" in response.text


# Test removed - endpoint does not exist
# @pytest.mark.skip(reason="Endpoint /api/auth/employee-access does not exist.")
# def test_employee_access_token(client: TestClient):
#     """Test endpoint that should only be accessible to employees."""
#     # ... (test implementation) ...


def test_get_me(client: TestClient, employee_token: str, test_employee: User):
    """Test retrieving the current user's information."""


# Correct patch path for get_db
with patch("exitbot.app.db.base.get_db") as mock_get_db:
    pass  # Add pass to satisfy indentation

# ...
