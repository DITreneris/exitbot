#!/usr/bin/env python
"""
Staging Deployment Validation Script for Predefined Questions System

This script performs comprehensive validation of the predefined questions implementation
in the staging environment before production deployment.

Features:
- Performance benchmarking (response times, throughput)
- Data integrity validation
- Feature verification
- Automated testing of critical paths

Usage:
    python validate_staging_deployment.py [--config CONFIG_FILE]

Environment Variables:
    STAGING_API_URL - URL of the staging API
    ADMIN_EMAIL - Admin user email for testing
    ADMIN_PASSWORD - Admin user password
    TEST_EMPLOYEE_EMAIL - Test employee email
    TEST_EMPLOYEE_NAME - Test employee name
"""

import os
import sys
import json
import time
import logging
import argparse
import requests
import statistics
from datetime import datetime
from typing import Dict, Any, Tuple

# Parse arguments first
parser = argparse.ArgumentParser(
    description="Validate staging deployment of predefined questions"
)
parser.add_argument(
    "--iterations", type=int, default=5, help="Number of test iterations to run"
)
parser.add_argument(
    "--api-url",
    type=str,
    default=os.getenv("STAGING_API_URL", "http://localhost:8000"),
    help="API URL to test against",
)
parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
args = parser.parse_args()

# Configure logging (use basicConfig for script simplicity)
log_level = logging.DEBUG if args.verbose else logging.INFO
logging.basicConfig(level=log_level, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("DeploymentValidator")  # Assign to logger

# Configuration - Read from environment variables with defaults
STAGING_API_URL = os.getenv("STAGING_API_URL", "http://localhost:8000")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "password")
TEST_EMPLOYEE_EMAIL = os.getenv("TEST_EMPLOYEE_EMAIL", "test.employee@example.com")
TEST_EMPLOYEE_NAME = os.getenv("TEST_EMPLOYEE_NAME", "Test Employee")

# Performance thresholds
PERFORMANCE_THRESHOLDS = {
    "interview_creation_ms": 1000,  # Max 1 second
    "message_response_ms": 500,  # Max 500ms
    "completion_ms": 1000,  # Max 1 second
}


class ValidationError(Exception):
    """Custom exception for validation failures"""

    pass


class ValidationRunner:
    """Runs validation tests for predefined questions system"""

    def __init__(self, api_url: str):
        self.api_url = api_url
        self.admin_token = None
        self.employee_token = None
        self.employee_id = None
        self.test_interviews = []
        self.performance_results = {}
        self.latest_responses = []

    def login_admin(self, email: str, password: str) -> str:
        """Login as admin and return token"""
        logger.info(f"Logging in as admin: {email}")
        try:
            response = requests.post(
                f"{self.api_url}/api/auth/login",
                data={"username": email, "password": password},
                timeout=10,
            )
            response.raise_for_status()
            token = response.json().get("access_token")
            if not token:
                raise ValidationError("No token in admin login response")

            self.admin_token = token
            logger.info("Admin login successful")
            return token
        except requests.exceptions.RequestException as e:
            logger.error(f"Admin login failed: {str(e)}")
            raise ValidationError(f"Admin login failed: {str(e)}")

    def get_employee_access(self, email: str, name: str) -> Tuple[str, int]:
        """Get employee access token and ID"""
        logger.info(f"Getting access for employee: {name}")
        try:
            response = requests.post(
                f"{self.api_url}/api/auth/employee-access",
                json={"email": email, "full_name": name},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
            token = data.get("access_token")
            employee_id = data.get("employee_id")

            if not token or not employee_id:
                raise ValidationError("Invalid employee access response")

            self.employee_token = token
            self.employee_id = employee_id
            logger.info(f"Employee access successful, ID: {employee_id}")
            return token, employee_id
        except requests.exceptions.RequestException as e:
            logger.error(f"Employee access failed: {str(e)}")
            raise ValidationError(f"Employee access failed: {str(e)}")

    def create_interview(
        self, token: str, employee_id: int, title: str = "Validation Test"
    ) -> int:
        """Create a new interview and return ID"""
        logger.info(f"Creating interview for employee {employee_id}")
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.api_url}/api/interviews/start",
                headers={"Authorization": f"Bearer {token}"},
                json={
                    "employee_id": employee_id,
                    "title": title,
                    "status": "scheduled",
                    "exit_date": datetime.now().isoformat().split("T")[0],
                },
                timeout=10,
            )
            creation_time = (time.time() - start_time) * 1000  # ms

            # Track performance
            if "interview_creation_ms" not in self.performance_results:
                self.performance_results["interview_creation_ms"] = []
            self.performance_results["interview_creation_ms"].append(creation_time)

            response.raise_for_status()
            data = response.json()
            interview_id = data.get("id")

            if not interview_id:
                raise ValidationError("No interview ID in response")

            # Check for initial question
            responses = data.get("responses", [])
            if not responses or len(responses) == 0:
                raise ValidationError("No initial question in new interview")

            # Track created interview for cleanup
            self.test_interviews.append(interview_id)

            logger.info(
                f"Interview created with ID {interview_id} in {creation_time:.2f}ms"
            )
            return interview_id
        except requests.exceptions.RequestException as e:
            logger.error(f"Interview creation failed: {str(e)}")
            raise ValidationError(f"Interview creation failed: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during interview creation: {e}")
            raise ValidationError(f"Unexpected error during interview creation: {e}")

    def send_message(
        self, token: str, interview_id: int, message: str
    ) -> Dict[str, Any]:
        """Send a message to an interview and return response data"""
        logger.info(f"Sending message to interview {interview_id}")
        try:
            start_time = time.time()
            response = requests.post(
                f"{self.api_url}/api/interviews/{interview_id}/message",
                headers={"Authorization": f"Bearer {token}"},
                json={"message": message},
                timeout=10,
            )
            response_time = (time.time() - start_time) * 1000  # ms

            # Track performance
            if "message_response_ms" not in self.performance_results:
                self.performance_results["message_response_ms"] = []
            self.performance_results["message_response_ms"].append(response_time)

            response.raise_for_status()
            data = response.json()

            # Validate response structure
            required_fields = [
                "content",
                "is_complete",
                "question_number",
                "total_questions",
            ]
            for field in required_fields:
                if field not in data:
                    raise ValidationError(f"Missing '{field}' in message response")

            logger.info(f"Message sent successfully in {response_time:.2f}ms")
            self.latest_responses.append(data)
            return data
        except requests.exceptions.RequestException as e:
            logger.error(f"Message sending failed: {str(e)}")
            raise ValidationError(f"Message sending failed: {str(e)}")

    def complete_interview(self, token: str, interview_id: int) -> bool:
        """Complete an entire interview by answering all questions"""
        logger.info(f"Completing full interview {interview_id}")
        try:
            # First, get interview details to find current state
            response = requests.get(
                f"{self.api_url}/api/interviews/{interview_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()

            # Get total question count from a message response
            message_response = self.send_message(
                token, interview_id, "Initial test message"
            )
            total_questions = message_response.get("total_questions")

            if not total_questions:
                raise ValidationError("Could not determine total question count")

            # Send messages until completion
            start_time = time.time()
            last_response = None
            question_number = message_response.get("question_number", 1)

            while question_number < total_questions:
                response_data = self.send_message(
                    token, interview_id, f"Test answer for question {question_number}"
                )
                last_response = response_data

                if response_data.get("is_complete", False):
                    break

                question_number = response_data.get(
                    "question_number", question_number + 1
                )

            completion_time = (time.time() - start_time) * 1000  # ms

            # Track performance
            if "completion_ms" not in self.performance_results:
                self.performance_results["completion_ms"] = []
            self.performance_results["completion_ms"].append(completion_time)

            # Verify interview is marked as completed
            response = requests.get(
                f"{self.api_url}/api/interviews/{interview_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            response.raise_for_status()
            final_data = response.json()

            if final_data.get("status") != "COMPLETED":
                raise ValidationError(
                    f"Interview not marked as completed. Status: {final_data.get('status')}"
                )

            logger.info(
                f"Interview {interview_id} completed successfully in {completion_time:.2f}ms"
            )

            if not self.latest_responses:
                # initial_response_count = len(self.get_responses(interview_id))
                pass  # Placeholder if needed
            else:
                # current_response_count = len(self.get_responses(interview_id))
                pass  # Placeholder if needed

            # Validate response content (basic check)
            # Basic validation: Ensure the latest bot response exists and is not empty
            if self.latest_responses:
                # last_response = self.latest_responses[-1]
                if not last_response.get("bot_response"):
                    logger.error("  Empty bot response received.")
                    return False
            # ... more validation possible here ...

            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Interview completion failed: {str(e)}")
            raise ValidationError(f"Interview completion failed: {str(e)}")

    def analyze_performance(self) -> Dict[str, Dict[str, float]]:
        """Analyze performance metrics"""
        logger.info("Analyzing performance metrics")
        stats = {}

        for metric, values in self.performance_results.items():
            if not values:
                continue

            metric_stats = {
                "avg": statistics.mean(values),
                "min": min(values),
                "max": max(values),
                "median": statistics.median(values),
            }

            # Add 95th percentile if we have enough samples
            if len(values) >= 5:
                metric_stats["p95"] = sorted(values)[int(0.95 * len(values))]

            stats[metric] = metric_stats

            # Check against thresholds
            threshold = PERFORMANCE_THRESHOLDS.get(metric)
            if threshold and metric_stats["avg"] > threshold:
                logger.warning(
                    f"Performance warning: {metric} average ({metric_stats['avg']:.2f}ms) exceeds threshold ({threshold}ms)"  # Threshold check
                )

        return stats

    def cleanup(self):
        """Clean up test data"""
        if not self.admin_token:
            logger.warning("No admin token available for cleanup")
            return

        logger.info(f"Cleaning up {len(self.test_interviews)} test interviews")

        for interview_id in self.test_interviews:
            try:
                # For now, just log cleanup - actual deletion might not be needed
                # or might require custom endpoints depending on your API
                logger.info(f"Would delete interview {interview_id}")

                # Example deletion code:
                # response = requests.delete(
                #     f"{self.api_url}/api/interviews/{interview_id}",
                #     headers={"Authorization": f"Bearer {self.admin_token}"},
                #     timeout=10
                # )
                # response.raise_for_status()
            except Exception as e:
                logger.warning(f"Cleanup failed for interview {interview_id}: {str(e)}")

    def run_validation(self, num_iterations: int = 5) -> bool:
        """Run the full validation suite"""
        success = False

        try:
            # Step 1: Login as admin
            self.login_admin(ADMIN_EMAIL, ADMIN_PASSWORD)

            # Step 2: Get employee access
            self.get_employee_access(TEST_EMPLOYEE_EMAIL, TEST_EMPLOYEE_NAME)

            # Step 3: Create and test multiple interviews
            logger.info(f"Running {num_iterations} test iterations")

            for i in range(num_iterations):
                logger.info(f"Starting iteration {i+1}/{num_iterations}")

                # Create new interview
                interview_id = self.create_interview(
                    self.employee_token, self.employee_id, f"Validation Test {i+1}"
                )

                # Test question progression
                for j in range(3):  # Test first 3 questions
                    response_data = self.send_message(
                        self.employee_token,
                        interview_id,
                        f"Test answer for iteration {i+1}, question {j+1}",
                    )

                    # Verify expected question number
                    expected_question = (
                        j + 2
                    )  # +2 because we start at Q1 and each answer advances us
                    if response_data.get("question_number") != expected_question:
                        raise ValidationError(
                            f"Incorrect question number: expected {expected_question}, "
                            f"got {response_data.get('question_number')}"
                        )

                # For the last iteration, complete the entire interview
                if i == num_iterations - 1:
                    self.complete_interview(self.employee_token, interview_id)

            # Step 4: Analyze performance
            performance_stats = self.analyze_performance()
            logger.info(
                f"Performance results: {json.dumps(performance_stats, indent=2)}"
            )

            # Step 5: Output summary report
            logger.info("===== VALIDATION SUMMARY =====")
            logger.info(f"Total iterations: {num_iterations}")
            logger.info(f"Total interviews created: {len(self.test_interviews)}")

            for metric, stats in performance_stats.items():
                threshold = PERFORMANCE_THRESHOLDS.get(metric)
                status = (
                    "✅ PASS"
                    if threshold and stats["avg"] <= threshold
                    else "⚠️ WARNING"
                )
                logger.info(
                    f"{metric}: avg={stats['avg']:.2f}ms, p95={stats.get('p95', 'N/A')}ms - {status}"
                )

            logger.info("============================")
            logger.info("✅ Validation successful")
            success = True

        except ValidationError as e:
            logger.error(f"❌ Validation failed: {str(e)}")
        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}")
        finally:
            # Always try to clean up
            try:
                self.cleanup()
            except Exception as e:
                logger.warning(f"Cleanup failed: {str(e)}")

        return success


def main():
    # Remove argument parsing from main, as it's done above
    # parser = argparse.ArgumentParser(
    #     description="Validate staging deployment of predefined questions"
    # )
    # parser.add_argument(
    #     "--iterations", type=int, default=5, help="Number of test iterations to run"
    # )
    # parser.add_argument(
    #     "--api-url", type=str, default=STAGING_API_URL, help="API URL to test against"
    # )
    # args = parser.parse_args()

    logger.info(f"Starting staging validation against {args.api_url}")
    logger.info(f"Running {args.iterations} test iterations")

    validator = ValidationRunner(args.api_url)
    success = validator.run_validation(args.iterations)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
