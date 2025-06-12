"""
Test file focused on API edge cases and error handling
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import patch, MagicMock
from datetime import timedelta
import logging # Import logging

from exitbot.app.main import app
from exitbot.app.db.models import User, Interview

# Use relative import for mocks within the same directory
from .mocks import MockLLM
from exitbot.app.db.crud import create_interview
from exitbot.app.db.models import InterviewStatus

client = TestClient(app)

# Initialize logger for this test module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG) # Basic config for testing


@pytest.fixture(scope="function")
def mock_llm():
    """Patch LLM client for testing"""
    with MockLLM.patch_llm():
        with MockLLM.patch_sentiment():
            yield


class TestEdgeCases:
    """Test class focused on handling edge cases and error conditions"""

    def test_invalid_interview_id(self, client, admin_token):
        """Test API response for non-existent interview ID"""
        response = client.get(
            "/api/interviews/999999", headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 404

        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_unauthorized_interview_access(
        self, client, employee_token, admin_token, test_db
    ):
        """Test unauthorized access attempt to another employee's interview"""
        # First create an interview for a different employee
        other_employee = User(
            email="other@example.com",
            hashed_password="hashed_pwd",
            full_name="Other Employee",
            department="Testing",
        )
        test_db.add(other_employee)
        test_db.commit()

        # Create interview for this other employee
        interview = Interview(employee_id=other_employee.id, status="in_progress")
        test_db.add(interview)
        test_db.commit()

        # Try to access it with a different employee's token
        response = client.get(
            f"/api/interviews/{interview.id}",
            headers={"Authorization": f"Bearer {employee_token}"},
        )

        assert response.status_code == 403
        assert (
            "not enough permissions to access this interview"
            in response.json()["detail"].lower()
        )

        # Admin should be able to access it
        admin_response = client.get(
            f"/api/interviews/{interview.id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert admin_response.status_code == 200

    def test_malformed_request_body(self, client, admin_token):
        """Test handling of malformed request bodies"""
        # Send POST to /api/interviews/ with missing required fields
        response = client.post(
            "/api/interviews/",  # Target the actual creation endpoint
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"title": "Missing employee ID"},  # Missing required employee_id
        )

        print(f"Malformed Body Response Status: {response.status_code}")
        try:
            print(f"Malformed Body Response JSON: {response.json()}")
        except Exception:
            print(f"Malformed Body Response Text: {response.text}")

        assert response.status_code == 422  # Unprocessable Entity
        # Check specific validation error if desired
        assert "field required" in response.text.lower()
        assert "employee_id" in response.text.lower()

    def test_expired_token(self, client, expired_token):
        """Test handling of expired authentication tokens"""
        response = client.get(
            "/api/interviews", headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401
        assert "invalid authentication credentials" in response.json()["detail"].lower()

    def test_invalid_query_params(self, client, admin_token):
        """Test handling of invalid query parameters"""
        # Test with invalid date format for /api/dashboard/export-data
        response = client.get(
            "/api/dashboard/export-data?start_date=invalid-date-format",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        print(f"Invalid Query Param Response Status: {response.status_code}")
        try:
            print(f"Invalid Query Param Response JSON: {response.json()}")
        except Exception:
            print(f"Invalid Query Param Response Text: {response.text}")

        assert response.status_code == 422
        # Check for validation error details if needed
        response_text = response.text.lower()
        assert "input should be a valid datetime" in response_text
        assert "start_date" in response_text

    def test_interview_completion_idempotency(
        self,
        client: TestClient,
        admin_token_user: str,
        test_db: Session,
        test_employee: User,
    ):
        """Test that completing an already completed interview is idempotent using real fixtures."""
        # Create an interview first
        interview = create_interview(
            db=test_db,
            employee_id=test_employee.id,
            title="Idempotency Test Interview",
            status=InterviewStatus.IN_PROGRESS,  # Start as in-progress
        )
        interview_id = interview.id

        complete_payload = {"status": InterviewStatus.COMPLETED.value}

        # First attempt to complete the interview
        response1 = client.put(
            f"/api/interviews/{interview_id}",  # Use standard update endpoint
            headers={"Authorization": f"Bearer {admin_token_user}"},
            json=complete_payload,
        )

        assert response1.status_code == 200
        assert response1.json()["status"] == "completed"

        # Verify in DB
        test_db.refresh(interview)
        assert interview.status == InterviewStatus.COMPLETED
        completed_at_first = interview.completed_at
        assert completed_at_first is not None

        # Try to complete it again
        response2 = client.put(
            f"/api/interviews/{interview_id}",  # Use standard update endpoint
            headers={"Authorization": f"Bearer {admin_token_user}"},
            json=complete_payload,
        )

        # Should still succeed and return the completed status
        assert response2.status_code == 200
        assert response2.json()["status"] == "completed"

        # Verify in DB again - status should remain completed, timestamp ideally unchanged
        test_db.refresh(interview)
        assert interview.status == InterviewStatus.COMPLETED
        completed_at_second = interview.completed_at
        assert (
            completed_at_second == completed_at_first
        )  # Timestamp shouldn't change ideally


# Correct patch path for get_current_user
with patch("exitbot.app.auth.get_current_user") as mock_get_current_user:
    pass  # Add pass to satisfy indentation

    # ...
