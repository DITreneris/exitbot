"""
Test file for API endpoints
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from fastapi import status
from sqlalchemy.orm import Session
import logging # Import logging

from exitbot.app.main import app
from exitbot.app.core.security import create_access_token
from exitbot.app.db.models import User, Interview
from exitbot.app.schemas.interview import InterviewCreate, InterviewStatus
from exitbot.app.db import crud
from exitbot.app.schemas.message import MessageRole
from exitbot.app.core.config import settings

# Initialize logger for this test module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG) # Basic config for testing

# Test client
client = TestClient(app)


class TestAPIEndpoints:
    """Test class for API endpoints"""

    @pytest.fixture
    def test_token(self):
        """Fixture for test token"""
        return create_access_token(subject_email="test@example.com", is_admin=False)

    @pytest.fixture
    def admin_token(self):
        """Fixture for admin token"""
        return create_access_token(subject_email="admin@example.com", is_admin=True)

    @pytest.fixture
    def mock_db_session(self):
        """Fixture for mocking database session"""
        with patch("exitbot.app.db.base.get_db") as mock_get_db:
            db_session = MagicMock()
            mock_get_db.return_value = db_session
            yield db_session

    def test_health_check(self):
        """Test health check endpoint"""
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_register_user(self, client: TestClient, test_db: Session):
        """Test user registration endpoint using real fixtures."""
        # Define unique user data for this test run
        user_email = f"new_user_{datetime.now().timestamp()}@example.com"
        user_data = {
            "email": user_email,
            "password": "StrongPassword123!",
            "full_name": "New User Name",
            # Add other fields required by UserCreate schema if any
        }

        # Call the registration endpoint
        response = client.post("/api/users/", json=user_data)

        print(f"Register Response Status: {response.status_code}")
        try:
            print(f"Register Response JSON: {response.json()}")
        except Exception:
            print(f"Register Response Text: {response.text}")

        # Assert successful creation (201 Created)
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["email"] == user_email
        assert response_data["full_name"] == user_data["full_name"]
        assert "id" in response_data  # Check if ID is returned

        # Verify user exists in the database
        db_user = test_db.query(User).filter(User.email == user_email).first()
        assert db_user is not None
        assert db_user.full_name == user_data["full_name"]
        # We can't easily check the password hash here without the raw password
        # but we can check that it's not None/empty
        assert db_user.hashed_password is not None
        assert len(db_user.hashed_password) > 0

    def test_register_duplicate_user(self, client: TestClient, test_db: Session):
        """Test registration with duplicate email using real fixtures."""
        # Define unique user data for this test run
        user_email = f"duplicate_user_{datetime.now().timestamp()}@example.com"
        user_data = {
            "email": user_email,
            "password": "DuplicatePass123!",
            "full_name": "Duplicate User Name",
        }

        # First registration attempt (should succeed)
        response1 = client.post("/api/users/", json=user_data)
        assert response1.status_code == 201

        # Verify user exists in the database after first attempt
        db_user = test_db.query(User).filter(User.email == user_email).first()
        assert db_user is not None

        # Second registration attempt with the same email (should fail)
        response2 = client.post("/api/users/", json=user_data)

        print(f"Duplicate Register Response Status: {response2.status_code}")
        try:
            print(f"Duplicate Register Response JSON: {response2.json()}")
        except Exception:
            print(f"Duplicate Register Response Text: {response2.text}")

        # Assert failure with 400 Bad Request
        assert response2.status_code == 400
        response_data = response2.json()
        assert "detail" in response_data
        # Check if the specific error message is returned (case-insensitive)
        assert "email already registered" in response_data["detail"].lower()

    def test_current_user(
        self, client: TestClient, test_employee: User, employee_token: str
    ):
        """Test current user endpoint using real fixtures."""
        # --- Remove mocking ---
        # The employee_token fixture handles creating a valid token for test_employee
        # The client fixture handles dependency overrides for get_db

        # Call the /api/users/me endpoint with the employee's token
        response = client.get(
            "/api/users/me", headers={"Authorization": f"Bearer {employee_token}"}
        )

        print(f"Current User Response Status: {response.status_code}")
        try:
            print(f"Current User Response JSON: {response.json()}")
        except Exception:
            print(f"Current User Response Text: {response.text}")

        # Assert successful response
        assert response.status_code == 200

        # Verify the returned data matches the test_employee fixture
        data = response.json()
        assert data["id"] == test_employee.id
        assert data["email"] == test_employee.email
        assert data["full_name"] == test_employee.full_name
        assert data["is_admin"] == test_employee.is_admin
        # Check other relevant fields if necessary
        assert data["department"] == test_employee.department

    def test_create_interview(
        self,
        client: TestClient,
        test_db: Session,
        test_admin_user: User,
        admin_token_user: str,
        test_employee: User,
    ):
        """Test interview creation endpoint using real fixtures."""

        # --- Remove mocking ---

        # Prepare interview data using the test_employee fixture
        interview_data = {
            "employee_id": test_employee.id,
            "title": f"Test Interview for {test_employee.full_name}",
            # Add other required fields from InterviewCreate schema if any
            # e.g., "exit_date": (datetime.now() + timedelta(days=10)).isoformat()
        }

        # Call the endpoint as the admin user
        response = client.post(
            "/api/interviews/",
            json=interview_data,
            headers={"Authorization": f"Bearer {admin_token_user}"},
        )

        print(f"Create Interview Response Status: {response.status_code}")
        try:
            print(f"Create Interview Response JSON: {response.json()}")
        except Exception:
            print(f"Create Interview Response Text: {response.text}")

        # Assert successful creation
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["employee_id"] == test_employee.id
        assert response_data["title"] == interview_data["title"]
        assert response_data["created_by_id"] == test_admin_user.id  # Verify creator
        assert "id" in response_data
        interview_id = response_data["id"]

        # Verify interview exists in the database
        db_interview = (
            test_db.query(Interview).filter(Interview.id == interview_id).first()
        )
        assert db_interview is not None
        assert db_interview.employee_id == test_employee.id
        assert db_interview.title == interview_data["title"]
        assert db_interview.created_by_id == test_admin_user.id
        assert db_interview.status == InterviewStatus.SCHEDULED  # Check default status

    def test_get_interview(
        self,
        client: TestClient,
        test_db: Session,
        test_admin_user: User,
        admin_token_user: str,
        test_employee: User,
    ):
        """Test get interview endpoint using real fixtures."""

        # --- Remove mocking ---

        # Create an interview first
        interview_title = f"Interview for Get Test - {test_employee.full_name}"
        interview = crud.create_interview(
            db=test_db,
            employee_id=test_employee.id,
            title=interview_title,
            created_by_id=test_admin_user.id,
            status=InterviewStatus.IN_PROGRESS,  # Set a specific status
        )
        interview_id = interview.id

        # Call the endpoint as admin to get the created interview
        response = client.get(
            f"/api/interviews/{interview_id}",
            headers={"Authorization": f"Bearer {admin_token_user}"},
        )

        print(f"Get Interview Response Status: {response.status_code}")
        try:
            print(f"Get Interview Response JSON: {response.json()}")
        except Exception:
            print(f"Get Interview Response Text: {response.text}")

        # Assert successful retrieval
        assert response.status_code == 200

        # Verify the data matches the created interview
        data = response.json()
        assert data["id"] == interview_id
        assert data["employee_id"] == test_employee.id
        assert data["title"] == interview_title
        assert data["created_by_id"] == test_admin_user.id
        assert (
            data["status"] == InterviewStatus.IN_PROGRESS.value
        )  # Check the status we set

    def test_get_nonexistent_interview(self, client: TestClient, admin_token_user: str):
        """Test getting a nonexistent interview using real fixtures."""

        # --- Remove mocking ---

        non_existent_id = 99999  # Use an ID that is unlikely to exist

        # Call the endpoint as admin (or employee) to get the non-existent interview
        response = client.get(
            f"/api/interviews/{non_existent_id}",
            headers={"Authorization": f"Bearer {admin_token_user}"},  # Use admin token
        )

        print(f"Get Nonexistent Interview Response Status: {response.status_code}")
        try:
            print(f"Get Nonexistent Interview Response JSON: {response.json()}")
        except Exception:
            print(f"Get Nonexistent Interview Response Text: {response.text}")

        # Assert 404 Not Found
        assert response.status_code == 404
        response_data = response.json()
        assert "detail" in response_data
        assert "interview not found" in response_data["detail"].lower()

    def test_list_interviews(
        self, client, test_db: Session, admin_token_user, test_employee, test_admin_user
    ):
        """Test listing interviews endpoint using real DB session."""
        # Clear any existing interviews to ensure a clean state
        test_db.query(Interview).delete()
        test_db.commit()

        # Create a couple of interviews directly in the test database
        interview1 = Interview(
            employee_id=test_employee.id,
            title="Test Interview 1",
            status=InterviewStatus.COMPLETED,
            created_by_id=test_admin_user.id,  # Assuming admin creates it
        )
        interview2 = Interview(
            employee_id=test_employee.id,  # Assuming same employee for simplicity
            title="Test Interview 2",
            status=InterviewStatus.SCHEDULED,
            created_by_id=test_admin_user.id,  # Assuming admin creates it
        )
        test_db.add_all([interview1, interview2])
        test_db.commit()
        test_db.refresh(interview1)
        test_db.refresh(interview2)

        response = client.get(
            "/api/interviews/", headers={"Authorization": f"Bearer {admin_token_user}"}
        )
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)  # Check if it's a dictionary (paginated response)
        assert "items" in data
        assert "total" in data
        assert isinstance(data["items"], list)
        assert data["total"] == 2  # Should now find the two created interviews

        # Verify the data in the response (adjust based on your Pydantic schema output)
        # Sorting by ID to ensure consistent order for comparison
        items = data["items"]  # Get the list of interviews
        items.sort(key=lambda x: x["id"])

        assert items[0]["title"] == "Test Interview 1"
        assert items[0]["status"] == "completed"
        assert items[0]["employee_id"] == test_employee.id
        assert items[1]["title"] == "Test Interview 2"
        assert items[1]["status"] == "scheduled"
        assert items[1]["employee_id"] == test_employee.id

    def test_update_interview(
        self, client, test_db, admin_token_user, test_employee, test_admin_user
    ):
        """Test updating interview endpoint using real DB session."""
        # Create an interview to update
        interview_to_update = Interview(
            employee_id=test_employee.id,
            title="Interview To Be Updated",
            status=InterviewStatus.SCHEDULED,
            created_by_id=test_admin_user.id,
        )
        test_db.add(interview_to_update)
        test_db.commit()
        test_db.refresh(interview_to_update)
        interview_id = interview_to_update.id

        update_data = {
            "status": InterviewStatus.IN_PROGRESS.value,  # Use enum value
            "title": "Updated Interview Title",
        }

        response = client.put(
            f"/api/interviews/{interview_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token_user}"},  # Use admin token
        )
        assert response.status_code == 200

        updated_data = response.json()
        assert updated_data["id"] == interview_id
        assert updated_data["status"] == InterviewStatus.IN_PROGRESS.value
        assert updated_data["title"] == "Updated Interview Title"

        # Verify changes in the database
        test_db.refresh(interview_to_update)
        assert interview_to_update.status == InterviewStatus.IN_PROGRESS
        assert interview_to_update.title == "Updated Interview Title"

    def test_delete_interview(
        self, client, test_db: Session, admin_token_user, test_employee, test_admin_user
    ):
        """Test deleting an interview endpoint using real fixtures"""
        # Create an interview first
        interview = Interview(
            employee_id=test_employee.id,
            status=InterviewStatus.SCHEDULED,
            created_by_id=test_admin_user.id,
            title="Interview To Be Deleted",
        )
        test_db.add(interview)
        # Commit first to get the ID assigned by the database
        test_db.commit()
        # Then refresh to load the committed state, including the ID
        test_db.refresh(interview)

        interview_id = interview.id  # Get the ID after commit/refresh

        # Verify it exists before deletion
        interview_before = (
            test_db.query(Interview).filter(Interview.id == interview_id).first()
        )
        assert interview_before is not None

        # Make the delete request
        response = client.delete(
            f"/api/interviews/{interview_id}",
            headers={
                "Authorization": f"Bearer {admin_token_user}"
            },  # Use the token directly
        )

        # Assert the response
        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["id"] == interview_id
        assert response_data["status"] == InterviewStatus.SCHEDULED.value

        # Verify it's deleted from the DB
        # Refresh the session state before querying
        test_db.expire_all()  # Expire all instances to force reload from DB on next access
        interview_after = (
            test_db.query(Interview).filter(Interview.id == interview_id).first()
        )
        assert interview_after is None

    @patch("exitbot.app.llm.factory.LLMClientFactory.create_client")
    def test_send_message(
        self,
        mock_create_client,
        client: TestClient,
        test_db: Session,
        test_employee: User,
        employee_token: str,
    ):
        """Test send message endpoint using real DB session and user fixtures."""
        # Mock LLM Client
        mock_llm = MagicMock()
        mock_llm.chat.return_value = "This is the AI response."
        mock_create_client.return_value = mock_llm

        # Create an interview manually in the test DB for the test_employee
        interview_to_create = InterviewCreate(
            employee_id=test_employee.id,
            title="Interview for Send Message Test",
            status=InterviewStatus.IN_PROGRESS,
        )
        # Pass arguments individually, not as a schema object
        created_interview = crud.create_interview(
            db=test_db,
            employee_id=interview_to_create.employee_id,
            title=interview_to_create.title,
            # exit_date=interview_to_create.exit_date, # Pass if needed/defined in schema
            status=interview_to_create.status,
        )
        interview_id = created_interview.id  # Get the ID of the created interview

        # Send message using the created interview's ID
        message_data = {"role": MessageRole.USER.value, "content": "Hello there!"}
        response = client.post(
            f"/api/interviews/{interview_id}/messages",  # Use the dynamic interview_id
            json=message_data,
            headers={"Authorization": f"Bearer {employee_token}"},  # Use employee token
        )

        print(f"Response Status Code: {response.status_code}")
        try:
            print(f"Response JSON: {response.json()}")
        except Exception:
            print(f"Response Text: {response.text}")  # Print text if not JSON

        assert response.status_code == 200  # Check for 200 OK
        data = response.json()
        assert data["content"] == "This is the AI response."
        assert data["role"] == MessageRole.ASSISTANT.value  # Use enum value

        # Optional: Verify messages were saved in DB (more complex assertion)
        # user_message = test_db.query(models.Message).filter(...).first()
        # assistant_message = test_db.query(models.Message).filter(...).first()
        # assert user_message is not None
        # assert assistant_message is not None

    def test_get_interview_messages(
        self,
        client: TestClient,
        test_db: Session,
        test_employee: User,
        employee_token: str,
    ):
        """Test get interview messages endpoint using real DB session and user fixtures."""

        # Create an interview for the test_employee
        interview = crud.create_interview(
            db=test_db,
            employee_id=test_employee.id,
            title="Interview for Get Messages Test",
            status=InterviewStatus.IN_PROGRESS,
        )
        interview_id = interview.id

        # Create some Response records associated with the interview
        response1_data = {
            "interview_id": interview_id,
            "employee_message": "User message 1",
            "bot_response": "Assistant response 1",
            "created_at": datetime.now() - timedelta(minutes=10),
        }
        response2_data = {
            "interview_id": interview_id,
            "employee_message": "User message 2",
            "bot_response": "Assistant response 2",
            "created_at": datetime.now() - timedelta(minutes=5),
        }
        crud.create_response(db=test_db, response_data=response1_data)
        crud.create_response(db=test_db, response_data=response2_data)

        # Call the correct endpoint GET /api/interviews/{id}/messages
        response = client.get(
            f"/api/interviews/{interview_id}/messages",
            headers={"Authorization": f"Bearer {employee_token}"},
        )

        print(f"Response Status Code: {response.status_code}")
        try:
            print(f"Response JSON: {response.json()}")
        except Exception:
            print(f"Response Text: {response.text}")

        assert response.status_code == 200

        # The endpoint returns a list of MessageSchema objects, reconstructed from Response entries
        # Expect 4 messages total (1 user + 1 assistant per Response entry)
        data = response.json()
        assert len(data) == 4
        assert data[0]["role"] == "user"
        assert data[0]["content"] == "User message 1"
        assert data[1]["role"] == "assistant"
        assert data[1]["content"] == "Assistant response 1"
        assert data[2]["role"] == "user"
        assert data[2]["content"] == "User message 2"
        assert data[3]["role"] == "assistant"
        assert data[3]["content"] == "Assistant response 2"

    def test_role_based_access_control(
        self,
        client: TestClient,
        test_employee: User,
        employee_token: str,
        test_admin_user: User,
        admin_token_user: str,
    ):
        """Test role-based access control using real fixtures and correct endpoint."""

        # --- No longer need to mock users or get_current_user ---
        # --- Fixtures handle user creation and tokens ---

        # Define the admin endpoint to test
        admin_endpoint = "/api/dashboard/statistics"  # Use a known admin endpoint

        # Test employee accessing admin endpoint (should fail with 403)
        print(
            f"Testing employee access to {admin_endpoint} with token {employee_token[:10]}..."
        )
        response_employee = client.get(
            admin_endpoint, headers={"Authorization": f"Bearer {employee_token}"}
        )
        print(f"Employee Response Status: {response_employee.status_code}")
        try:
            print(f"Employee Response JSON: {response_employee.json()}")
        except Exception:
            print(f"Employee Response Text: {response_employee.text}")

        # get_current_active_superuser dependency should raise 403
        assert response_employee.status_code == 403

        # Test admin accessing admin endpoint (should succeed with 200)
        print(
            f"Testing admin access to {admin_endpoint} with token {admin_token_user[:10]}..."
        )
        response_admin = client.get(
            admin_endpoint, headers={"Authorization": f"Bearer {admin_token_user}"}
        )
        print(f"Admin Response Status: {response_admin.status_code}")
        try:
            print(f"Admin Response JSON: {response_admin.json()}")
        except Exception:
            print(f"Admin Response Text: {response_admin.text}")

        # Endpoint should succeed for admin
        assert response_admin.status_code == 200
        # Optionally, check basic structure of the response
        data = response_admin.json()
        assert "total_users" in data
        assert "total_interviews" in data


# Mock the generate_interview_summary function from the ReportingService
# @patch("exitbot.app.services.reporting.ReportingService.generate_interview_summary")
# def test_submit_interview_success(mock_generate_summary, test_client, mocker):
#     pass

# Mock the generate_interview_summary function from the ReportingService
# @patch("exitbot.app.services.reporting.ReportingService.generate_interview_summary")
# def test_submit_interview_invalid_employee_id(mock_generate_summary, test_client):
#     pass

# Mock the generate_interview_summary function from the ReportingService
# @patch("exitbot.app.services.reporting.ReportingService.generate_interview_summary")
# def test_submit_interview_already_submitted(mock_generate_summary, test_client, mocker):
#     pass

# Mock the generate_interview_summary function from the ReportingService
# @patch("exitbot.app.services.reporting.ReportingService.generate_interview_summary")
# def test_submit_interview_report_generation_error(mock_generate_summary, test_client, mocker):
#     pass

# Mock the generate_interview_summary function from the ReportingService
# @patch("exitbot.app.services.reporting.ReportingService.generate_interview_summary")
# def test_get_hr_report_success(mock_generate_summary, test_client, mocker):
#     pass

# Mock the generate_interview_summary function from the ReportingService
# @patch("exitbot.app.services.reporting.ReportingService.generate_interview_summary")
# def test_get_hr_report_not_found(mock_generate_summary, test_client, mocker):
#     pass

# Ensure the user is created correctly in the mock database
# mock_db_session.add(test_user)
# mock_db_session.commit()

# # Patch the user creation logic to simulate an existing user
# # with patch("exitbot.app.db.crud.get_user_by_email") as mock_get_by_email:
# #     mock_get_by_email.return_value = test_user

# #     # Attempt to create the same user again
# #     response = client.post(
# #         "/api/users/",
# #         json={
# #             "email": "existing@example.com",
# #             "password": "strongpassword",
# #             "full_name": "Existing User",
# #             "role": "employee"
# #         }
# #     )
# #     assert response.status_code == 400
# #     assert "Email already registered" in response.json()["detail"]
