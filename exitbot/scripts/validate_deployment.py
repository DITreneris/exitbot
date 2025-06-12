#!/usr/bin/env python
"""
Predefined Questions Deployment Validation Script

This script tests the core functionality of the predefined questions implementation
to ensure readiness for deployment. It checks:

1. Backend API endpoints
2. Question retrieval
3. Interview progression
4. Error handling

Run this script against your staging environment before deploying to production.
"""

import os
import sys
import requests
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("predefined_questions_validation.log"),
    ],
)

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "password")
TEST_EMPLOYEE_EMAIL = os.getenv("TEST_EMPLOYEE_EMAIL", "test.employee@example.com")
TEST_EMPLOYEE_NAME = os.getenv("TEST_EMPLOYEE_NAME", "Test Employee")


class ValidationError(Exception):
    """Error during validation"""

    pass


def login(email, password):
    """Login to get access token"""
    logging.info(f"Logging in as {email}")
    try:
        response = requests.post(
            f"{API_URL}/api/auth/login",
            data={"username": email, "password": password},
            timeout=10,
        )
        response.raise_for_status()
        token = response.json().get("access_token")
        if not token:
            raise ValidationError("No token in login response")
        return token
    except requests.exceptions.RequestException as e:
        logging.error(f"Login failed: {str(e)}")
        raise ValidationError(f"Login failed: {str(e)}")


def get_employee_access(email, name):
    """Get employee access token"""
    logging.info(f"Getting access for employee {name}")
    try:
        response = requests.post(
            f"{API_URL}/api/employees/access",
            json={"email": email, "name": name},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        token = data.get("access_token")
        employee_id = data.get("employee_id")
        if not token or not employee_id:
            raise ValidationError("Invalid employee access response")
        return token, employee_id
    except requests.exceptions.RequestException as e:
        logging.error(f"Employee access failed: {str(e)}")
        raise ValidationError(f"Employee access failed: {str(e)}")


def create_interview(token, employee_id):
    """Create a new interview"""
    logging.info(f"Creating interview for employee {employee_id}")
    try:
        response = requests.post(
            f"{API_URL}/api/interviews/start",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "employee_id": employee_id,
                "title": "Validation Test",
                "status": "scheduled",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        interview_id = data.get("id")
        if not interview_id:
            raise ValidationError("No interview ID in response")

        # Check for initial question
        responses = data.get("responses", [])
        if not responses or len(responses) == 0:
            raise ValidationError("No initial question in new interview")

        logging.info(f"Interview created with ID {interview_id}")
        return interview_id
    except requests.exceptions.RequestException as e:
        logging.error(f"Interview creation failed: {str(e)}")
        raise ValidationError(f"Interview creation failed: {str(e)}")


def test_question_progression(token, interview_id, num_questions=3):
    """Test progressing through questions"""
    logging.info(f"Testing question progression for interview {interview_id}")
    try:
        for i in range(num_questions):
            response = requests.post(
                f"{API_URL}/api/interviews/{interview_id}/message",
                headers={"Authorization": f"Bearer {token}"},
                json={"message": f"Test answer {i+1}"},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            # Validate response structure
            if "content" not in data:
                raise ValidationError(f"Missing 'content' in response {i+1}")
            if "is_complete" not in data:
                raise ValidationError(f"Missing 'is_complete' in response {i+1}")
            if "question_number" not in data:
                raise ValidationError(f"Missing 'question_number' in response {i+1}")
            if "total_questions" not in data:
                raise ValidationError(f"Missing 'total_questions' in response {i+1}")

            # Check question progression
            if data.get("question_number") != i + 2:
                raise ValidationError(
                    f"Incorrect question number: expected {i+2}, got {data.get('question_number')}"
                )

            logging.info(
                f"Successfully progressed to question {data.get('question_number')}"
            )
    except requests.exceptions.RequestException as e:
        logging.error(f"Question progression failed: {str(e)}")
        raise ValidationError(f"Question progression failed: {str(e)}")


def test_interview_completion(token, interview_id, total_questions):
    """Test completing an interview"""
    logging.info(f"Testing interview completion for interview {interview_id}")
    try:
        # Get current progress
        response = requests.get(
            f"{API_URL}/api/interviews/{interview_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()
        responses = data.get("responses", [])
        current_question = len(responses)

        # Answer remaining questions
        for i in range(current_question, total_questions):
            response = requests.post(
                f"{API_URL}/api/interviews/{interview_id}/message",
                headers={"Authorization": f"Bearer {token}"},
                json={"message": f"Final answer {i+1}"},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            # Check if we've completed
            if data.get("is_complete", False):
                logging.info("Interview successfully completed")
                return True

        # Verify interview status
        response = requests.get(
            f"{API_URL}/api/interviews/{interview_id}",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("status") != "COMPLETED":
            raise ValidationError(
                f"Interview not marked as completed. Status: {data.get('status')}"
            )

        logging.info("Interview completion verified")
        return True
    except requests.exceptions.RequestException as e:
        logging.error(f"Interview completion failed: {str(e)}")
        raise ValidationError(f"Interview completion failed: {str(e)}")


def validate_deployment():
    """Run validation tests"""
    logging.info("Starting predefined questions deployment validation")

    try:
        # --- Admin Login (Optional, if admin actions needed later) ---
        admin_token = login(ADMIN_EMAIL, ADMIN_PASSWORD)
        if admin_token:
            logging.info("  Admin login successful.")
            # Store admin_token if needed for later validation steps
            # self.admin_token = admin_token
        else:
            logging.warning("  Admin login failed. Skipping admin-only checks.")
            # Optionally, fail validation if admin login is critical
            # return False

        # --- Run Interview ---
        # Get employee access
        employee_token, employee_id = get_employee_access(
            TEST_EMPLOYEE_EMAIL, TEST_EMPLOYEE_NAME
        )
        logging.info(f"Employee access successful, ID: {employee_id}")

        # Create interview
        interview_id = create_interview(employee_token, employee_id)

        # Test question progression
        test_question_progression(employee_token, interview_id)

        # Test completing an interview (create a new one)
        new_interview_id = create_interview(employee_token, employee_id)
        test_interview_completion(employee_token, new_interview_id, 20)

        logging.info(
            "✅ Validation successful! The predefined questions implementation is ready for deployment."
        )
        return True
    except ValidationError as e:
        logging.error(f"❌ Validation failed: {str(e)}")
        return False
    except Exception as e:
        logging.error(f"❌ Unexpected error during validation: {str(e)}")
        return False


if __name__ == "__main__":
    success = validate_deployment()
    sys.exit(0 if success else 1)
