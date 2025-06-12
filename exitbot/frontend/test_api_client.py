"""
Tests for the frontend API client module.
"""

import pytest
import requests

# Remove unused requests_mock
# import requests_mock
# Remove unused datetime, timedelta, date
# from datetime import datetime, timedelta, date
# Remove unused os
# import os
# Remove unused logging
# import logging
import json

# Module to test
from exitbot.frontend import api_client

# Mock API URL for consistency
MOCK_API_URL = "http://mock-api.test"

# --- Fixtures ---


@pytest.fixture(autouse=True)
def set_mock_api_url(monkeypatch):
    """Set the API_URL environment variable and reload module for tests."""
    monkeypatch.setenv("API_URL", MOCK_API_URL)
    import importlib

    importlib.reload(api_client)
    # Clear cache before each test to ensure isolation
    # This assumes @st.cache_data is used on relevant functions
    # You might need to explicitly clear specific caches if not all use it
    functions_with_cache = [
        api_client.get_all_interviews,
        api_client.get_interview_details,
        api_client.get_interview_summary,
        api_client.get_summary_stats,
        api_client.get_department_breakdown,
        api_client.get_questions,
    ]
    for func in functions_with_cache:
        if hasattr(func, "clear"):
            func.clear()


@pytest.fixture
def mock_token():
    """Provide a mock token for authenticated requests."""
    return "fake_test_token"


# --- Helper Functions ---


def assert_error_details(
    error_details, expected_status=None, expected_detail_contains=None
):
    """Assert the structure and content of the error details dictionary."""
    assert error_details is not None, "Error details should not be None"
    assert isinstance(error_details, dict), "Error details should be a dictionary"
    assert "status" in error_details, "Error details should contain 'status'"
    assert "detail" in error_details, "Error details should contain 'detail'"
    assert "raw_text" in error_details, "Error details should contain 'raw_text'"
    if expected_status:
        assert (
            error_details["status"] == expected_status
        ), f"Expected status {expected_status}, got {error_details['status']}"
    if expected_detail_contains:
        assert (
            expected_detail_contains in error_details["detail"]
        ), f"Expected detail '{expected_detail_contains}' not found in '{error_details['detail']}'"


# --- Test Cases ---


# --- Authentication Tests (Updated) ---
def test_login_success(requests_mock):
    """Test successful login API call returns (token, None)."""
    mock_response = {"access_token": "fake_success_token", "token_type": "bearer"}
    requests_mock.post(
        f"{MOCK_API_URL}/api/auth/login", json=mock_response, status_code=200
    )

    token, error = api_client.login("test@example.com", "password123")
    assert token == "fake_success_token"
    assert error is None


def test_login_failure_unauthorized(requests_mock):
    """Test failed login API call (wrong password) returns (None, error_details)."""
    raw_error_text = "Incorrect email or password"
    requests_mock.post(
        f"{MOCK_API_URL}/api/auth/login", text=raw_error_text, status_code=401
    )

    token, error = api_client.login("test@example.com", "wrongpassword")
    assert token is None
    assert_error_details(
        error, expected_status=401, expected_detail_contains="Authentication failed"
    )
    assert error["raw_text"] == raw_error_text


def test_login_connection_error(requests_mock):
    """Test login API call with connection error returns (None, error_details)."""
    requests_mock.post(
        f"{MOCK_API_URL}/api/auth/login", exc=requests.exceptions.ConnectTimeout
    )

    token, error = api_client.login("test@example.com", "password123")
    assert token is None
    assert_error_details(
        error, expected_status=None, expected_detail_contains="Could not connect"
    )


# --- Interview List Tests (Updated) ---
def test_get_all_interviews_success(requests_mock, mock_token):
    """Test fetching all interviews successfully returns (data, None)."""
    mock_data = [
        {"id": 1, "employee_id": 101, "status": "completed"},
        {"id": 2, "employee_id": 102, "status": "in_progress"},
    ]
    requests_mock.get(
        f"{MOCK_API_URL}/api/interviews?skip=0&limit=100",
        json=mock_data,
        status_code=200,
    )

    interviews, error = api_client.get_all_interviews(mock_token)
    assert interviews == mock_data
    assert error is None


def test_get_all_interviews_failure_500(requests_mock, mock_token):
    """Test fetching all interviews with 500 error returns (None, error_details)."""
    requests_mock.get(
        f"{MOCK_API_URL}/api/interviews?skip=0&limit=100",
        status_code=500,
        text="Server Error",
    )

    interviews, error = api_client.get_all_interviews(mock_token)
    assert interviews is None
    assert_error_details(
        error, expected_status=500, expected_detail_contains="Server error"
    )


# --- Interview Detail Tests (Updated) ---
def test_get_interview_details_success(requests_mock, mock_token):
    """Test fetching interview details successfully returns (data, None)."""
    interview_id = 5
    mock_data = {"id": interview_id, "employee_id": 105, "status": "completed"}
    requests_mock.get(
        f"{MOCK_API_URL}/api/interviews/{interview_id}", json=mock_data, status_code=200
    )

    details, error = api_client.get_interview_details(mock_token, interview_id)
    assert details == mock_data
    assert error is None


def test_get_interview_details_not_found_404(requests_mock, mock_token):
    """Test fetching non-existent interview details returns (None, error_details)."""
    interview_id = 999
    requests_mock.get(
        f"{MOCK_API_URL}/api/interviews/{interview_id}",
        status_code=404,
        text="Not Found",
    )

    details, error = api_client.get_interview_details(mock_token, interview_id)
    assert details is None
    assert_error_details(
        error, expected_status=404, expected_detail_contains="resource not found"
    )


# --- Interview Summary Tests (New) ---
def test_get_interview_summary_success(requests_mock, mock_token):
    """Test fetching interview summary successfully returns (text, None)."""
    interview_id = 7
    mock_summary = "This is the interview summary."
    requests_mock.get(
        f"{MOCK_API_URL}/api/reports/interview/{interview_id}/summary",
        text=mock_summary,
        status_code=200,
    )

    summary, error = api_client.get_interview_summary(mock_token, interview_id)
    assert summary == mock_summary
    assert error is None


def test_get_interview_summary_not_available_404(requests_mock, mock_token):
    """Test fetching summary that is not yet available (404) returns (message, None)."""
    interview_id = 8
    requests_mock.get(
        f"{MOCK_API_URL}/api/reports/interview/{interview_id}/summary",
        status_code=404,
        text="Not Found",
    )

    summary, error = api_client.get_interview_summary(mock_token, interview_id)
    assert "not yet available" in summary
    assert error is None  # Special case: 404 for summary is not treated as an error


def test_get_interview_summary_failure_500(requests_mock, mock_token):
    """Test fetching summary with 500 error returns (None, error_details)."""
    interview_id = 9
    requests_mock.get(
        f"{MOCK_API_URL}/api/reports/interview/{interview_id}/summary",
        status_code=500,
        text="Processing Error",
    )

    summary, error = api_client.get_interview_summary(mock_token, interview_id)
    assert summary is None
    assert_error_details(
        error, expected_status=500, expected_detail_contains="Server error"
    )


# --- Summary Stats Tests (New) ---
def test_get_summary_stats_success(requests_mock, mock_token):
    """Test fetching summary stats successfully returns (data, None)."""
    mock_data = {"total_interviews": 10, "completed_interviews": 8}
    requests_mock.get(
        f"{MOCK_API_URL}/api/reports/summary", json=mock_data, status_code=200
    )

    stats, error = api_client.get_summary_stats(mock_token)
    assert stats == mock_data
    assert error is None


def test_get_summary_stats_failure_403(requests_mock, mock_token):
    """Test fetching summary stats with 403 error returns (None, error_details)."""
    requests_mock.get(
        f"{MOCK_API_URL}/api/reports/summary", status_code=403, text="Forbidden"
    )

    stats, error = api_client.get_summary_stats(mock_token)
    assert stats is None
    assert_error_details(
        error, expected_status=403, expected_detail_contains="Authorization denied"
    )


# --- Department Breakdown Tests (New) ---
def test_get_department_breakdown_success(requests_mock, mock_token):
    """Test fetching department breakdown successfully returns (data, None)."""
    mock_data = {"departments": [{"department": "Sales", "interview_count": 5}]}
    requests_mock.get(
        f"{MOCK_API_URL}/api/reports/by-department", json=mock_data, status_code=200
    )

    data, error = api_client.get_department_breakdown(mock_token)
    assert data == mock_data
    assert error is None


# --- Export Data Tests (New) ---
def test_export_data_success(requests_mock, mock_token):
    """Test exporting data successfully returns (content, None)."""
    mock_content = b'{"key": "value"}'
    requests_mock.get(
        f"{MOCK_API_URL}/api/reports/export?format=json",
        content=mock_content,
        status_code=200,
    )

    content, error = api_client.export_data(mock_token, format="json")
    assert content == mock_content
    assert error is None


# --- Question Management Tests (New) ---


def test_get_questions_success(requests_mock, mock_token):
    """Test fetching questions successfully returns (data, None)."""
    mock_data = [
        {"id": 1, "text": "Why are you leaving?", "is_active": True},
        {"id": 2, "text": "What did you like best?", "is_active": True},
    ]
    matcher = requests_mock.get(
        f"{MOCK_API_URL}/api/questions/", json=mock_data, status_code=200
    )

    questions, error = api_client.get_questions(mock_token)
    assert questions == mock_data
    assert error is None
    assert matcher.called_once  # Check it was called


def test_get_questions_failure_500(requests_mock, mock_token):
    """Test fetching questions with 500 error returns (None, error_details)."""
    requests_mock.get(
        f"{MOCK_API_URL}/api/questions/", status_code=500, text="DB Error"
    )

    questions, error = api_client.get_questions(mock_token)
    assert questions is None
    assert_error_details(
        error, expected_status=500, expected_detail_contains="Server error"
    )


def test_create_question_success(requests_mock, mock_token):
    """Test creating a question successfully returns (data, None) and clears cache."""
    question_text = "What could be improved?"
    mock_response = {"id": 3, "text": question_text, "is_active": True}
    post_matcher = requests_mock.post(
        f"{MOCK_API_URL}/api/questions/", json=mock_response, status_code=201
    )
    # Mock the GET request that will happen after cache clear
    get_matcher = requests_mock.get(
        f"{MOCK_API_URL}/api/questions/", status_code=200, json=[mock_response]
    )

    result, error = api_client.create_question(mock_token, question_text)
    assert result == mock_response
    assert error is None
    assert post_matcher.last_request.json() == {
        "text": question_text,
        "is_active": True,
    }

    # Call get_questions again to see if cache was cleared (mock should be called again)
    api_client.get_questions(mock_token)
    # Check that the GET mock was called *after* the POST, implying cache clear worked
    assert (
        get_matcher.call_count >= 1
    )  # Needs to be called at least once after the POST


def test_create_question_failure_400(requests_mock, mock_token):
    """Test creating a question with 400 error returns (None, error_details)."""
    question_text = ""  # Example invalid input
    raw_error_text = "Text cannot be empty"
    requests_mock.post(
        f"{MOCK_API_URL}/api/questions/", status_code=400, text=raw_error_text
    )

    result, error = api_client.create_question(mock_token, question_text)
    assert result is None
    assert_error_details(
        error, expected_status=400, expected_detail_contains="Text cannot be empty"
    )  # Check parsed detail
    assert error["raw_text"] == raw_error_text


def test_update_question_success(requests_mock, mock_token):
    """Test updating a question successfully returns (data, None) and clears cache."""
    question_id = 1
    updated_text = "New question text?"
    mock_response = {"id": question_id, "text": updated_text, "is_active": True}
    put_matcher = requests_mock.put(
        f"{MOCK_API_URL}/api/questions/{question_id}",
        json=mock_response,
        status_code=200,
    )
    get_matcher = requests_mock.get(
        f"{MOCK_API_URL}/api/questions/", status_code=200, json=[mock_response]
    )

    result, error = api_client.update_question(
        mock_token, question_id, question_text=updated_text
    )
    assert result == mock_response
    assert error is None
    assert put_matcher.last_request.json() == {"text": updated_text}

    # Check cache clear
    api_client.get_questions(mock_token)
    assert get_matcher.call_count >= 1


def test_update_question_not_found_404(requests_mock, mock_token):
    """Test updating non-existent question returns (None, error_details)."""
    question_id = 99
    requests_mock.put(
        f"{MOCK_API_URL}/api/questions/{question_id}", status_code=404, text="Not Found"
    )

    result, error = api_client.update_question(mock_token, question_id, is_active=False)
    assert result is None
    assert_error_details(
        error, expected_status=404, expected_detail_contains="resource not found"
    )


def test_delete_question_success(requests_mock, mock_token):
    """Test deleting a question successfully returns (True, None) and clears cache."""
    question_id = 2
    delete_matcher = requests_mock.delete(
        f"{MOCK_API_URL}/api/questions/{question_id}", status_code=204
    )
    get_matcher = requests_mock.get(
        f"{MOCK_API_URL}/api/questions/", status_code=200, json=[]
    )

    result, error = api_client.delete_question(mock_token, question_id)
    assert result is True
    assert error is None
    assert delete_matcher.called_once

    # Check cache clear
    api_client.get_questions(mock_token)
    assert get_matcher.call_count >= 1


def test_delete_question_not_found_404(requests_mock, mock_token):
    """Test deleting non-existent question returns (True, None) - treated as success."""
    question_id = 99
    requests_mock.delete(
        f"{MOCK_API_URL}/api/questions/{question_id}", status_code=404, text="Not Found"
    )

    result, error = api_client.delete_question(mock_token, question_id)
    assert result is True  # Deleting non-existent is idempotent, treated as success
    assert error is None


def test_delete_question_failure_500(requests_mock, mock_token):
    """Test deleting question with 500 error returns (None, error_details)."""
    question_id = 1
    requests_mock.delete(
        f"{MOCK_API_URL}/api/questions/{question_id}",
        status_code=500,
        text="Deletion Failed",
    )

    result, error = api_client.delete_question(mock_token, question_id)
    assert result is None  # Should return None for error
    assert_error_details(
        error, expected_status=500, expected_detail_contains="Server error"
    )


# --- Employee Access Tests (Updated) ---
def test_get_employee_access_details_success(requests_mock):
    """Test successful employee access returns (data, None)."""
    mock_data = {
        "access_token": "emp_token",
        "employee_id": 123,
        "token_type": "bearer",
    }
    payload = {"email": "e@c.co", "full_name": "Emp Name", "department": "Dept"}
    requests_mock.post(
        f"{MOCK_API_URL}/api/auth/employee-access", json=mock_data, status_code=200
    )

    # Need to call the function from the reloaded module instance
    result, error = api_client.get_employee_access_details(**payload)
    assert result == mock_data
    assert error is None


def test_get_employee_access_details_failure_409(requests_mock):
    """Test failed employee access (409 Conflict) returns (None, error_details)."""
    payload = {"email": "e@c.co", "full_name": "Wrong Name", "department": "Dept"}
    # Simulate FastAPI error response structure
    mock_error_json = {
        "detail": "Provided name does not match existing record for this email."
    }
    requests_mock.post(
        f"{MOCK_API_URL}/api/auth/employee-access",
        json=mock_error_json,
        status_code=409,
    )

    result, error = api_client.get_employee_access_details(**payload)
    assert result is None
    # Check specific detail parsed from JSON
    assert_error_details(
        error,
        expected_status=409,
        expected_detail_contains="Provided name does not match",
    )
    # Check raw text is the original JSON string
    assert error["raw_text"] == json.dumps(mock_error_json)


# --- Remaining TODOs from original file ---
# TODO: Add tests for employee flow functions (imported into employee_app):
# - create_interview_session (if it exists in api_client)
# - send_interview_message (if it exists in api_client)
