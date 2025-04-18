import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
from jose import jwt
from unittest.mock import patch, MagicMock
import json
from sqlalchemy.orm import Session

from exitbot.app.api_utils import APIResponse, APIError, success_response, error_response, APIException
from exitbot.app.core.security import create_access_token, verify_password, get_password_hash, ALGORITHM
from exitbot.app.db.models import User, Interview, InterviewStatus # Assuming Interview model exists
from exitbot.app.core.config import settings
from exitbot.app.schemas import UserCreate # Assuming UserCreate schema is needed
from exitbot.app.db.crud.user import get_user # Import for patching
from exitbot.app.llm.factory import LLMClientFactory # Import for patching
from exitbot.app.db import crud # Import crud directly

def test_api_response_model():
    """Test API response model"""
    response = APIResponse(
        status="success",
        message="Test message",
        data={"test": "data"}
    )
    
    assert response.status == "success"
    assert response.message == "Test message"
    assert response.data == {"test": "data"}
    assert isinstance(response.timestamp, str)

def test_api_error_model():
    """Test API error model"""
    error = APIError(
        message="Test error",
        error_code="TEST_ERROR",
        details={"field": "value"}
    )
    
    assert error.status == "error"
    assert error.message == "Test error"
    assert error.error_code == "TEST_ERROR"
    assert error.details == {"field": "value"}
    assert isinstance(error.timestamp, str)

def test_success_response():
    """Test success response creation"""
    response = success_response(
        message="Test success",
        data={"test": "data"}
    )
    
    assert response.status_code == 200
    content = json.loads(response.body)
    assert content["status"] == "success"
    assert content["message"] == "Test success"
    assert content["data"] == {"test": "data"}

def test_error_response():
    """Test error response creation"""
    response = error_response(
        message="Test error",
        status_code=400,
        error_code="TEST_ERROR",
        details={"field": "value"}
    )
    
    assert response.status_code == 400
    content = json.loads(response.body)
    assert content["status"] == "error"
    assert content["message"] == "Test error"
    assert content["error_code"] == "TEST_ERROR"
    assert content["details"] == {"field": "value"}

def test_api_exception():
    """Test API exception"""
    with pytest.raises(APIException) as exc_info:
        raise APIException(
            message="Test exception",
            status_code=400,
            error_code="TEST_EXCEPTION"
        )
    
    assert exc_info.value.status_code == 400
    assert "Test exception" in str(exc_info.value.detail)

def test_password_hashing():
    """Test password hashing and verification"""
    password = "testpassword123"
    hashed = get_password_hash(password)
    
    assert verify_password(password, hashed)
    assert not verify_password("wrongpassword", hashed)

def test_token_creation():
    """Test JWT token creation"""
    email = "testuser@example.com"
    token = create_access_token(subject_email=email)
    
    # Verify token can be decoded
    decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
    assert decoded["sub"] == email
    assert "exp" in decoded

def test_login_success(client: TestClient, test_db: Session, test_employee: User):
    """Test successful login"""
    # Use the employee user fixture
    test_email = test_employee.email
    test_password = "EmpPassword1" # Correct password from conftest.py fixture

    # Patch crud.get_user_by_email to return the test user
    with patch("exitbot.app.db.crud.user.get_user_by_email", return_value=test_employee):
        # Patch verify_password to simulate correct password
        with patch("exitbot.app.core.security.verify_password", return_value=True):
            # Patch get_db dependency (adjust path if needed)
            # Assuming get_db is now in exitbot.app.dependencies or exitbot.app.db.base
            with patch("exitbot.app.db.base.get_db", return_value=test_db): # Updated patch target
                 response = client.post(
                    f"{settings.API_V1_PREFIX}/auth/login", # Use the correct login path
                    data={"username": test_email, "password": test_password}
                 )
                 assert response.status_code == 200, response.text
                 data = response.json()
                 assert "access_token" in data
                 assert data["token_type"] == "bearer"

def test_login_failure_wrong_password(client: TestClient, test_db: Session, test_employee: User):
    """Test login failure with wrong password"""
    test_email = test_employee.email

    with patch("exitbot.app.db.crud.user.get_user_by_email", return_value=test_employee):
        # Patch verify_password to simulate incorrect password
        with patch("exitbot.app.core.security.verify_password", return_value=False):
            with patch("exitbot.app.db.base.get_db", return_value=test_db): # Updated patch target
                response = client.post(
                    f"{settings.API_V1_PREFIX}/auth/login", # Use the correct login path
                    data={"username": test_email, "password": "wrongpassword"}
                )
                assert response.status_code == 401, response.text
                data = response.json()
                assert data["detail"] == "Incorrect email or password" # Check if error message matches API

def test_login_failure_user_not_found(client: TestClient, test_db: Session):
    """Test login failure when user does not exist"""
    with patch("exitbot.app.db.crud.user.get_user_by_email", return_value=None):
         with patch("exitbot.app.db.base.get_db", return_value=test_db): # Updated patch target
            response = client.post(
                f"{settings.API_V1_PREFIX}/auth/login", # Use the correct login path
                data={"username": "nonexistent@example.com", "password": "password"}
            )
            assert response.status_code == 401, response.text
            data = response.json()
            assert data["detail"] == "Incorrect email or password" # Check if error message matches API

def test_protected_endpoint_requires_auth(client: TestClient):
    """Test that a protected endpoint requires authentication"""
    # Replace '/users/me' with an actual protected endpoint if different
    response = client.get(f"{settings.API_V1_PREFIX}/users/me")
    assert response.status_code == 401, response.text
    # Check detail if needed: assert response.json()["detail"] == "Not authenticated"

def test_protected_endpoint_with_valid_token(client: TestClient, employee_token: str, test_employee: User):
    """Test access to protected endpoint with a valid token"""
    # Replace '/users/me' with an actual protected endpoint
    # This test assumes the /users/me endpoint exists and returns the current user
    with patch("exitbot.app.api.deps.get_current_active_user", return_value=test_employee): # Updated deps path
        response = client.get(
            f"{settings.API_V1_PREFIX}/users/me",
            headers={"Authorization": f"Bearer {employee_token}"}
        )
        assert response.status_code == 200, response.text
        data = response.json()
        # Adjust assertions based on the actual response structure of /users/me
        assert data["email"] == test_employee.email

def test_start_interview_requires_auth(client: TestClient):
    """Test /api/interviews/start requires authentication"""
    response = client.post(f"{settings.API_V1_PREFIX}/interviews/", json={"employee_id": 123}) # Assuming POST to /interviews/ creates one
    assert response.status_code == 401, response.text # Should fail without token

def test_start_interview_success_admin(client: TestClient, admin_token_user: str, test_db: Session, test_admin_user: User):
    """Test successful interview start with admin authentication"""
    employee_id_to_create = 999
    # Mock the employee user that the endpoint will look for
    mock_employee = User(
        id=employee_id_to_create,
        email=f"employee_{employee_id_to_create}@example.com",
        full_name="Mock Employee",
        is_admin=False
    )
    # Create a MagicMock mimicking the Interview ORM object
    # Add all attributes accessed by endpoint or needed for serialization
    mock_orm_interview = MagicMock(spec=Interview) # Use spec for better mocking
    mock_orm_interview.id = 1
    mock_orm_interview.employee_id = employee_id_to_create
    mock_orm_interview.created_by_id = test_admin_user.id
    mock_orm_interview.title = "Test Interview"
    mock_orm_interview.description = None
    mock_orm_interview.status = InterviewStatus.SCHEDULED # Use Enum member
    mock_orm_interview.start_date = None
    mock_orm_interview.scheduled_at = None
    mock_orm_interview.end_date = None
    mock_orm_interview.completed_at = None
    mock_orm_interview.exit_date = None
    mock_orm_interview.created_at = datetime.now() # Use datetime object
    mock_orm_interview.updated_at = None
    mock_orm_interview.interview_metadata = None
    # Ensure relationship attributes that might be accessed by Pydantic exist
    # Even if empty, their presence might be needed
    mock_orm_interview.responses = [] 
    # Add mock employee/creator if accessed via relationship during serialization
    # mock_orm_interview.employee = mock_employee 
    # mock_orm_interview.creator = test_admin_user
    
    # Apply patches using 'with' inside the test, targeting crud namespace
    with patch("exitbot.app.api.deps.get_current_active_user", return_value=test_admin_user),\
         patch.object(crud, 'get_user', return_value=mock_employee) as mock_get_employee,\
         patch.object(crud, 'create_interview', return_value=mock_orm_interview) as mock_create, \
         patch("exitbot.app.db.base.get_db", return_value=test_db):

        response = client.post(
            f"{settings.API_V1_PREFIX}/interviews/",
            headers={"Authorization": f"Bearer {admin_token_user}"},
            json={"employee_id": employee_id_to_create, "title": "Test Interview"}
        )
        # Expect 201 Created, as per endpoint decorator
        assert response.status_code == 201, response.text
        mock_get_employee.assert_called_once_with(test_db, user_id=employee_id_to_create)
        mock_create.assert_called_once()
        # Check args passed to create_interview
        args, kwargs = mock_create.call_args
        assert kwargs['db'] == test_db
        assert kwargs['employee_id'] == employee_id_to_create
        assert kwargs['title'] == "Test Interview"
        assert kwargs['created_by_id'] == test_admin_user.id

        data = response.json()
        # Assertions against the expected data (should match mock_orm_interview attributes)
        assert data["id"] == mock_orm_interview.id
        assert data["employee_id"] == mock_orm_interview.employee_id
        assert data["created_by_id"] == mock_orm_interview.created_by_id
        assert data["title"] == mock_orm_interview.title
        assert data["status"] == mock_orm_interview.status.value # Compare Enum value

def test_process_message_requires_auth(client: TestClient):
    """Test /api/interviews/{id}/message requires authentication"""
    # Assuming endpoint is /api/interviews/{interview_id}/messages/
    response = client.post(f"{settings.API_V1_PREFIX}/interviews/1/messages/", json={"content": "Test message"})
    assert response.status_code == 401, response.text

# Remove decorators for patches
# @patch("exitbot.app.llm.factory.LLMClientFactory.create_client")
# @patch("exitbot.app.db.crud.interview.get_interview")
# @patch("exitbot.app.api.deps.get_current_active_user")
def test_process_message_auth_works(
    # Remove mock args from signature
    # mock_get_user, mock_get_interview, mock_create_llm_client,
    client: TestClient, employee_token: str, test_employee: User, test_db: Session
):
    """Test processing a message with authentication, mocking the LLM call"""
    # Mock an existing interview linked to the employee
    mock_interview = Interview(
        id=1,
        employee_id=test_employee.id,
        status="in_progress",
        created_at=datetime.now(),
        title="Test Interview for Message"
    )
    # Configure the mock LLM client
    mock_llm = MagicMock()
    mock_llm.chat.return_value = "Mocked LLM chat response"

    # Apply patches using 'with' inside the test, targeting crud namespace
    with patch("exitbot.app.api.deps.get_current_active_user", return_value=test_employee) as mock_get_user,\
         patch.object(crud, 'get_interview', return_value=mock_interview) as mock_get_interview,\
         patch("exitbot.app.llm.factory.LLMClientFactory.create_client", return_value=mock_llm) as mock_create_llm_client,\
         patch("exitbot.app.db.base.get_db", return_value=test_db):

        response = client.post(
            f"{settings.API_V1_PREFIX}/interviews/1/messages/",
            headers={"Authorization": f"Bearer {employee_token}"},
            json={"content": "Hello from employee"}
        )

        assert response.status_code == 200, response.text
        mock_get_interview.assert_called_once_with(db=test_db, interview_id=1)
        mock_create_llm_client.assert_called_once()
        mock_llm.chat.assert_called_once()
        
        # Check response data
        data = response.json()
        assert data["role"] == "assistant"
        assert data["content"] == "Mocked LLM chat response"

def test_non_existent_endpoint(client: TestClient, employee_token: str):
    """Test accessing a non-existent endpoint"""
    response = client.get(
        f"{settings.API_V1_PREFIX}/non/existent/path",
        headers={"Authorization": f"Bearer {employee_token}"}
    )
    assert response.status_code == 404, response.text 