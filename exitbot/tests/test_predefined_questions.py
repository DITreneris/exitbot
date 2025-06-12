"""
Tests for the predefined questions API flow
"""
# Remove unused pytest
# import pytest
# Remove unused patch, MagicMock
from unittest.mock import patch, MagicMock
# Remove unused TestClient
# from fastapi.testclient import TestClient
# Remove unused Session
# from sqlalchemy.orm import Session

# Remove unused app
# from exitbot.app.main import app
# Remove unused User
# from exitbot.app.db.models import User, Interview
from exitbot.app.db.models import Interview  # Keep Interview
from exitbot.app.core import interview_questions

# Remove unused MessageSchema
# from exitbot.app.schemas.interview import MessageSchema
# Remove unused Response
# from exitbot.app.db.models import Response
from datetime import datetime
from exitbot.app.schemas.interview import InterviewStatus
import time
import logging # Import logging

# Initialize logger for this test module
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG) # Basic config for testing


@pytest.mark.usefixtures("test_db")

class TestPredefinedQuestions:
    """Test the predefined questions and helper functions"""

    def test_get_question_by_order(self):
        """Test retrieving questions by order number"""
        # Test valid question
        q1 = interview_questions.get_question_by_order(1)
        assert q1 is not None
        assert q1["id"] == 1
        assert isinstance(q1["text"], str)
        assert "category" in q1

        # Test middle question
        q10 = interview_questions.get_question_by_order(10)
        assert q10 is not None
        assert q10["id"] == 10

        # Test out of range - too low
        q_neg = interview_questions.get_question_by_order(-1)
        assert q_neg is None

        # Test out of range - too high
        q_high = interview_questions.get_question_by_order(999)
        assert q_high is None

    def test_get_question_by_id(self):
        """Test retrieving questions by ID"""
        # Test valid ID
        q1 = interview_questions.get_question_by_id(1)
        assert q1 is not None
        assert q1["id"] == 1

        # Test invalid ID
        q_invalid = interview_questions.get_question_by_id(999)
        assert q_invalid is None

    def test_get_question_count(self):
        """Test getting the total number of questions"""
        count = interview_questions.get_question_count()
        assert count > 0
        assert count == len(interview_questions.INTERVIEW_QUESTIONS)

    def test_get_all_questions(self):
        """Test getting all predefined questions"""
        questions = interview_questions.get_all_questions()
        assert len(questions) > 0
        assert isinstance(questions, list)
        assert "id" in questions[0]
        assert "text" in questions[0]
        assert "category" in questions[0]


class TestPredefinedQuestionsEdgeCases:
    """Test edge cases and error conditions for the predefined questions system"""

    def test_invalid_interview_id(self, client, test_db, employee_token):
        """Test sending a message to a non-existent interview ID"""
        invalid_id = 99999
        response = client.post(
            f"/api/interviews/{invalid_id}/message",
            headers={"Authorization": f"Bearer {employee_token}"},
            json={"message": "This interview doesn't exist."},
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_empty_message(self, client, test_db, test_employee, employee_token):
        """Test sending an empty message"""
        # Create an interview
        create_response = client.post(
            "/api/interviews/start",
            headers={"Authorization": f"Bearer {employee_token}"},
            json={"employee_id": test_employee.id, "title": "Empty Message Test"},
        )

        assert create_response.status_code == 200
        interview_id = create_response.json()["id"]

        # Send empty message
        response = client.post(
            f"/api/interviews/{interview_id}/message",
            headers={"Authorization": f"Bearer {employee_token}"},
            json={"message": ""},
        )

        # The API should still process this - empty answers are valid
        assert response.status_code == 200
        data = response.json()

        # Should progress to second question despite empty message
        assert data["question_number"] == 2

    def test_concurrent_messages(self, client, test_db, test_employee, employee_token):
        """Test handling concurrent messages by sending multiple messages quickly"""
        # Create an interview
        create_response = client.post(
            "/api/interviews/start",
            headers={"Authorization": f"Bearer {employee_token}"},
            json={"employee_id": test_employee.id, "title": "Concurrent Messages Test"},
        )

        assert create_response.status_code == 200
        interview_id = create_response.json()["id"]

        # Send multiple messages in quick succession
        responses = []
        for i in range(3):
            response = client.post(
                f"/api/interviews/{interview_id}/message",
                headers={"Authorization": f"Bearer {employee_token}"},
                json={"message": f"Concurrent message {i+1}"},
            )
            responses.append(response)

        # All requests should be processed successfully
        for i, response in enumerate(responses):
            assert response.status_code == 200
            data = response.json()
            # Each response should advance to the next question
            assert data["question_number"] == i + 2

    def test_invalid_access(self, client, test_db, test_employee, admin_token):
        """Test accessing an employee's interview with admin credentials (should work)"""
        # Create an interview for the employee
        create_response = client.post(
            "/api/interviews/start",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"employee_id": test_employee.id, "title": "Admin Access Test"},
        )

        assert create_response.status_code == 200
        interview_id = create_response.json()["id"]

        # Admin should be able to view the interview
        detail_response = client.get(
            f"/api/interviews/{interview_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
        )

        assert detail_response.status_code == 200

        # Admin should be able to send messages on behalf of employees
        message_response = client.post(
            f"/api/interviews/{interview_id}/message",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"message": "Message from admin"},
        )

        assert message_response.status_code == 200


class TestInterviewAPI:
    """Test the interview API endpoints with predefined questions"""

    def test_start_interview(self, client, test_db, test_employee, employee_token):
        """Test starting an interview and receiving the first question"""
        response = client.post(
            "/api/interviews/start",
            headers={"Authorization": f"Bearer {employee_token}"},
            json={
                "employee_id": test_employee.id,
                "title": "Exit Interview Test",
                "status": "scheduled",
                "exit_date": datetime.now().isoformat().split("T")[0],
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert "id" in data

        # Get the interview and check the first question was added
        interview_id = data["id"]
        interview_detail = client.get(
            f"/api/interviews/{interview_id}",
            headers={"Authorization": f"Bearer {employee_token}"},
        )

        assert interview_detail.status_code == 200
        detail_data = interview_detail.json()

        # Responses should have at least one entry - the first question
        assert "responses" in detail_data
        assert len(detail_data["responses"]) >= 1

        # The first response should match the first predefined question
        first_question = interview_questions.get_question_by_order(1)
        first_response = detail_data["responses"][0]
        assert first_response["bot_response"] == first_question["text"]

    def test_send_message_progression(
        self, client, test_db, test_employee, employee_token
    ):
        """Test sending a message and progressing through questions"""
        # First create an interview
        create_response = client.post(
            "/api/interviews/start",
            headers={"Authorization": f"Bearer {employee_token}"},
            json={
                "employee_id": test_employee.id,
                "title": "Question Progression Test",
                "status": "scheduled",
            },
        )

        assert create_response.status_code == 200
        interview_id = create_response.json()["id"]

        # Now send a message to progress to the second question
        message_response = client.post(
            f"/api/interviews/{interview_id}/message",
            headers={"Authorization": f"Bearer {employee_token}"},
            json={"message": "This is my answer to the first question."},
        )

        assert message_response.status_code == 200
        message_data = message_response.json()

        # Check the response contains the expected fields
        assert "content" in message_data
        assert "is_complete" in message_data
        assert "question_number" in message_data
        assert "total_questions" in message_data

        # Verify we're on the second question now
        second_question = interview_questions.get_question_by_order(2)
        assert message_data["content"] == second_question["text"]
        assert message_data["is_complete"] is False
        assert message_data["question_number"] == 2
        assert (
            message_data["total_questions"] == interview_questions.get_question_count()
        )

    def test_complete_interview(self, client, test_db, test_employee, employee_token):
        """Test completing all questions marks the interview as complete"""
        # Create an interview
        create_response = client.post(
            "/api/interviews/start",
            headers={"Authorization": f"Bearer {employee_token}"},
            json={
                "employee_id": test_employee.id,
                "title": "Interview Completion Test",
            },
        )

        assert create_response.status_code == 200
        interview_id = create_response.json()["id"]

        # Get the total number of questions to answer
        total_questions = interview_questions.get_question_count()

        # Answer all questions
        last_response = None
        for i in range(1, total_questions):
            response = client.post(
                f"/api/interviews/{interview_id}/message",
                headers={"Authorization": f"Bearer {employee_token}"},
                json={"message": f"This is my answer to question {i}."},
            )
            assert response.status_code == 200
            last_response = response.json()

        # The last response should indicate the interview is complete
        assert last_response["is_complete"] is True

        # Check the interview status was updated
        interview_detail = client.get(
            f"/api/interviews/{interview_id}",
            headers={"Authorization": f"Bearer {employee_token}"},
        )

        assert interview_detail.status_code == 200
        detail_data = interview_detail.json()
        assert detail_data["status"] == InterviewStatus.COMPLETED.value
        assert detail_data["completed_at"] is not None

    def test_already_completed_interview(
        self, client, test_db, test_employee, employee_token
    ):
        """Test that messaging a completed interview returns the completed message"""
        # Create and complete an interview
        create_response = client.post(
            "/api/interviews/start",
            headers={"Authorization": f"Bearer {employee_token}"},
            json={"employee_id": test_employee.id, "title": "Completed Interview Test"},
        )

        assert create_response.status_code == 200
        interview_id = create_response.json()["id"]

        # Manually mark the interview as completed
        interview = (
            test_db.query(Interview).filter(Interview.id == interview_id).first()
        )
        interview.status = InterviewStatus.COMPLETED.value
        interview.completed_at = datetime.now()
        test_db.commit()

        # Try to send a message to the completed interview
        response = client.post(
            f"/api/interviews/{interview_id}/message",
            headers={"Authorization": f"Bearer {employee_token}"},
            json={"message": "This should not be processed."},
        )

        assert response.status_code == 200
        data = response.json()

        # Should get the completion message
        assert "completed" in data["content"].lower()
        assert data["is_complete"] is True
