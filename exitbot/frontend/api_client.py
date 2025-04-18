"""
API Client for interacting with the ExitBot backend from Streamlit frontend apps.
Functions return a tuple: (result, error_details).
On success, result is the data, error_details is None.
On failure, result is None, error_details is a dict {'status': code, 'detail': msg, 'raw_text': txt}.
"""

import requests
# import streamlit as st # No longer directly using st.error/warning here
import os
import json
import logging
from datetime import timedelta, date, datetime
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# API connection settings - Read from environment variable
API_URL = os.getenv("API_URL", "http://localhost:8000")

def _parse_error(response: requests.Response) -> dict:
    """Helper to parse error details from response."""
    try:
        # Try parsing JSON, often contains a 'detail' field in FastAPI errors
        error_json = response.json()
        detail = error_json.get('detail', response.text)
    except json.JSONDecodeError:
        # If not JSON, use the raw text
        detail = response.text
        
    # Provide clearer messages for common statuses
    if response.status_code == 401:
        detail = "Authentication failed. Please check credentials or log in again."
    elif response.status_code == 403:
        detail = "Authorization denied. You do not have permission for this action."
    elif response.status_code == 404:
         detail = "Requested resource not found."
    elif response.status_code >= 500:
        detail = f"Server error ({response.status_code}). Please try again later or contact support."

    logging.warning(f"API Error: Status {response.status_code}, Response: {response.text}") # Log the raw error
    return {'status': response.status_code, 'detail': detail, 'raw_text': response.text}

def _handle_request_exception(e: Exception, operation: str) -> dict:
    """Helper to handle requests.exceptions.RequestException."""
    logging.error(f"Connection Error during {operation}: {str(e)}")
    return {'status': None, 'detail': f"Could not connect to the server during {operation}. Please check the connection and API URL.", 'raw_text': str(e)}


# --- Authentication --- 
def login(email, password):
    """Login to the API (for HR/Admin). Returns (token, None) or (None, error_details)."""
    operation = "login"
    try:
        response = requests.post(
            f"{API_URL}/api/auth/login",
            data={"username": email, "password": password},
            timeout=10 # Add a timeout
        )
        if response.status_code == 200:
            # Original code only returned access_token, let's return the full response maybe?
            # Or stick to just token for now.
            token = response.json().get("access_token")
            if token:
                 return token, None
            else:
                 # Should not happen if status is 200, but safety check
                 return None, {'status': 200, 'detail': 'Login successful but no token received.', 'raw_text': response.text}
        else:
            return None, _parse_error(response)
    except requests.exceptions.RequestException as e:
        return None, _handle_request_exception(e, operation)
    except Exception as e: # Catch other potential errors
        logging.error(f"Unexpected error during {operation}: {str(e)}")
        return None, {'status': None, 'detail': f"An unexpected error occurred during {operation}.", 'raw_text': str(e)}

# --- Interview Data --- 
# Note: @st.cache_data needs access to st, so we can't completely remove the import.
# Let's keep st import but remove direct st.error/warning calls. Re-import st.
import streamlit as st

@st.cache_data(ttl=timedelta(minutes=10))
def get_all_interviews(_token, skip=0, limit=100):
    """Fetch all interviews. Returns (interview_list, None) or (None, error_details)."""
    operation = "fetching all interviews"
    try:
        headers = {"Authorization": f"Bearer {_token}"}
        response = requests.get(
            f"{API_URL}/api/interviews?skip={skip}&limit={limit}",
            headers=headers,
            timeout=15
        )
        if response.status_code == 200:
            return response.json(), None
        else:
            # Return empty list on error for consistency? Or None? Let's return None.
            return None, _parse_error(response)
    except requests.exceptions.RequestException as e:
        return None, _handle_request_exception(e, operation)
    except Exception as e:
        logging.error(f"Unexpected error during {operation}: {str(e)}")
        return None, {'status': None, 'detail': f"An unexpected error occurred during {operation}.", 'raw_text': str(e)}


@st.cache_data(ttl=timedelta(minutes=5))
def get_interview_details(_token, interview_id):
    """Fetch interview details. Returns (interview_dict, None) or (None, error_details)."""
    operation = f"fetching details for interview {interview_id}"
    try:
        headers = {"Authorization": f"Bearer {_token}"}
        response = requests.get(
            f"{API_URL}/api/interviews/{interview_id}",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, _parse_error(response)
    except requests.exceptions.RequestException as e:
        return None, _handle_request_exception(e, operation)
    except Exception as e:
        logging.error(f"Unexpected error during {operation}: {str(e)}")
        return None, {'status': None, 'detail': f"An unexpected error occurred during {operation}.", 'raw_text': str(e)}


# --- Reporting / Summaries --- 
@st.cache_data(ttl=timedelta(minutes=5))
def get_interview_summary(_token, interview_id):
    """Fetch interview summary. Returns (summary_text, None) or (None, error_details)."""
    operation = f"fetching summary for interview {interview_id}"
    try:
        headers = {"Authorization": f"Bearer {_token}"}
        response = requests.get(
            f"{API_URL}/api/reports/interview/{interview_id}/summary",
            headers=headers,
            timeout=20 # Summary might take longer
        )
        if response.status_code == 200:
            return response.text, None # Summary might be just text
        elif response.status_code == 404:
             # Treat 404 not as an error, but as summary not ready
             return "Summary not yet available or generated.", None 
        else:
            return None, _parse_error(response)
    except requests.exceptions.RequestException as e:
        return None, _handle_request_exception(e, operation)
    except Exception as e:
        logging.error(f"Unexpected error during {operation}: {str(e)}")
        return None, {'status': None, 'detail': f"An unexpected error occurred during {operation}.", 'raw_text': str(e)}


@st.cache_data(ttl=timedelta(minutes=10))
def get_summary_stats(_token, start_date=None, end_date=None):
    """Fetch summary statistics. Returns (stats_dict, None) or (None, error_details)."""
    operation = "fetching summary stats"
    try:
        headers = {"Authorization": f"Bearer {_token}"}
        params = {}
        if start_date:
            params["start_date"] = start_date.isoformat() if isinstance(start_date, (date, datetime)) else start_date
        if end_date:
            params["end_date"] = end_date.isoformat() if isinstance(end_date, (date, datetime)) else end_date

        response = requests.get(
            f"{API_URL}/api/dashboard/statistics",
            headers=headers,
            params=params,
            timeout=15
        )
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, _parse_error(response)
    except requests.exceptions.RequestException as e:
        return None, _handle_request_exception(e, operation)
    except Exception as e:
        logging.error(f"Unexpected error during {operation}: {str(e)}")
        return None, {'status': None, 'detail': f"An unexpected error occurred during {operation}.", 'raw_text': str(e)}


@st.cache_data(ttl=timedelta(minutes=10))
def get_department_breakdown(_token, start_date=None, end_date=None):
    """Fetch department breakdown. Returns (dept_dict, None) or (None, error_details)."""
    operation = "fetching department breakdown"
    try:
        headers = {"Authorization": f"Bearer {_token}"}
        params = {}
        if start_date:
            params["start_date"] = start_date.isoformat() if isinstance(start_date, (date, datetime)) else start_date
        if end_date:
            params["end_date"] = end_date.isoformat() if isinstance(end_date, (date, datetime)) else end_date

        response = requests.get(
            f"{API_URL}/api/reports/by-department",
            headers=headers,
            params=params,
            timeout=15
        )
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, _parse_error(response)
    except requests.exceptions.RequestException as e:
        return None, _handle_request_exception(e, operation)
    except Exception as e:
        logging.error(f"Unexpected error during {operation}: {str(e)}")
        return None, {'status': None, 'detail': f"An unexpected error occurred during {operation}.", 'raw_text': str(e)}


# --- Data Export --- 
def export_data(token, format="json", start_date=None, end_date=None, department=None):
    """Export interview data. Returns (export_content, None) or (None, error_details)."""
    operation = "exporting data"
    try:
        headers = {"Authorization": f"Bearer {token}"}
        params = {"format": format}
        if start_date:
            params["start_date"] = start_date.isoformat() if isinstance(start_date, (date, datetime)) else start_date
        if end_date:
            params["end_date"] = end_date.isoformat() if isinstance(end_date, (date, datetime)) else end_date
        if department:
            params["department"] = department

        response = requests.get(
            f"{API_URL}/api/reports/export",
            headers=headers,
            params=params,
            timeout=30 # Export might take longer
        )
        if response.status_code == 200:
            return response.content, None # Return raw content for download handler
        else:
            return None, _parse_error(response)
    except requests.exceptions.RequestException as e:
        return None, _handle_request_exception(e, operation)
    except Exception as e:
        logging.error(f"Unexpected error during {operation}: {str(e)}")
        return None, {'status': None, 'detail': f"An unexpected error occurred during {operation}.", 'raw_text': str(e)}


# --- Question Management --- 

@st.cache_data(ttl=timedelta(minutes=5)) # Cache for a short time
def get_questions(_token):
    """Fetch all questions. Returns (question_list, None) or (None, error_details)."""
    operation = "fetching questions"
    try:
        headers = {"Authorization": f"Bearer {_token}"}
        response = requests.get(f"{API_URL}/api/questions/", headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json(), None
        else:
            # Return empty list or None? Let's go with None for errors.
            return None, _parse_error(response)
    except requests.exceptions.RequestException as e:
        return None, _handle_request_exception(e, operation)
    except Exception as e:
        logging.error(f"Unexpected error during {operation}: {str(e)}")
        return None, {'status': None, 'detail': f"An unexpected error occurred during {operation}.", 'raw_text': str(e)}


def create_question(token, question_text):
    """Create a new question. Returns (new_question_dict, None) or (None, error_details)."""
    operation = "creating question"
    try:
        headers = {"Authorization": f"Bearer {token}"}
        payload = {"text": question_text, "is_active": True} # Assuming default is active
        response = requests.post(f"{API_URL}/api/questions/", headers=headers, json=payload, timeout=10)
        if response.status_code == 201: # Created
            get_questions.clear() # Clear cache
            return response.json(), None
        else:
            return None, _parse_error(response)
    except requests.exceptions.RequestException as e:
        return None, _handle_request_exception(e, operation)
    except Exception as e:
        logging.error(f"Unexpected error during {operation}: {str(e)}")
        return None, {'status': None, 'detail': f"An unexpected error occurred during {operation}.", 'raw_text': str(e)}


def update_question(token, question_id, question_text=None, is_active=None):
    """Update question. Returns (updated_question_dict, None) or (None, error_details)."""
    operation = f"updating question {question_id}"
    try:
        headers = {"Authorization": f"Bearer {token}"}
        payload = {}
        if question_text is not None:
            payload["text"] = question_text
        if is_active is not None:
            payload["is_active"] = is_active
            
        if not payload: 
            return True, None # No update needed, return success-like state

        response = requests.put(f"{API_URL}/api/questions/{question_id}", headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            get_questions.clear() # Clear cache
            return response.json(), None
        else:
            return None, _parse_error(response)
    except requests.exceptions.RequestException as e:
        return None, _handle_request_exception(e, operation)
    except Exception as e:
        logging.error(f"Unexpected error during {operation}: {str(e)}")
        return None, {'status': None, 'detail': f"An unexpected error occurred during {operation}.", 'raw_text': str(e)}


def delete_question(token, question_id):
    """Delete question. Returns (True, None) or (None, error_details)."""
    operation = f"deleting question {question_id}"
    try:
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.delete(f"{API_URL}/api/questions/{question_id}", headers=headers, timeout=10)
        if response.status_code == 204: # No Content (Success)
            get_questions.clear() # Clear cache
            return True, None
        else:
            # Handle 404 gracefully? If trying to delete non-existent, maybe not an "error"
            if response.status_code == 404:
                 return True, None # Treat as success if already gone
            return None, _parse_error(response)
    except requests.exceptions.RequestException as e:
        return None, _handle_request_exception(e, operation)
    except Exception as e:
        logging.error(f"Unexpected error during {operation}: {str(e)}")
        return None, {'status': None, 'detail': f"An unexpected error occurred during {operation}.", 'raw_text': str(e)}

# --- Employee App Specific ---

def get_employee_access_details(email, full_name):
    """Get employee access token/ID. Returns (access_details_dict, None) or (None, error_details)."""
    operation = "getting employee access"
    payload = {
        "email": email,
        "full_name": full_name,
        # "department": department # Removed
    }
    try:
        # Check actual backend endpoint path
        # Correct path is /api/auth/employee-access handled by auth.py
        response = requests.post(f"{API_URL}/api/auth/employee-access", json=payload, timeout=20) # Increased timeout to 20s
        if response.status_code == 200:
            return response.json(), None
        else:
            # Provide more specific feedback for employee app validation errors (e.g., 409 Conflict)
            error_details = _parse_error(response)
            if response.status_code == 409: # Conflict (e.g., name/dept mismatch)
                # Try to get detail from the parsed error_details, fallback to generic message
                # Assumes _parse_error already tried to get 'detail' from JSON response if possible
                error_details['detail'] = error_details.get('detail', "A user with this email exists, but the provided name or department does not match.")
            return None, error_details
            
    except requests.exceptions.RequestException as e:
        return None, _handle_request_exception(e, operation)
    except Exception as e:
        logging.error(f"Unexpected error during {operation}: {str(e)}")
        return None, {'status': None, 'detail': f"An unexpected error occurred during {operation}.", 'raw_text': str(e)}

# --- System Configuration (Placeholders) ---

@st.cache_data(ttl=timedelta(minutes=15))
def get_system_config(_token):
    """Fetch system configuration settings. Returns (config_dict, None) or (None, error_details)."""
    operation = "fetching system configuration"
    # Placeholder: Replace with actual API call when backend endpoint exists
    # Example: url = f"{API_URL}/api/config/"
    # try:
    #     headers = {"Authorization": f"Bearer {_token}"}
    #     response = requests.get(url, headers=headers, timeout=10)
    #     if response.status_code == 200:
    #         return response.json(), None
    #     else:
    #         return None, _parse_error(response)
    # except requests.exceptions.RequestException as e:
    #     return None, _handle_request_exception(e, operation)
    # except Exception as e:
    #     logging.error(f"Unexpected error during {operation}: {str(e)}")
    #     return None, {'status': None, 'detail': f"An unexpected error occurred during {operation}.", 'raw_text': str(e)}
    logging.info(f"{operation}: Placeholder function called. Returning mock data.")
    # Return mock data for UI development
    mock_config = {
        "llm_model": "ollama/llama2",
        "sentiment_threshold_positive": 0.3,
        "sentiment_threshold_negative": -0.3,
        "default_report_format": "json"
    }
    return mock_config, None 

def update_system_config(token, config_data: dict):
    """Update system configuration settings. Returns (updated_config_dict, None) or (None, error_details)."""
    operation = "updating system configuration"
    # Placeholder: Replace with actual API call when backend endpoint exists
    # Example: url = f"{API_URL}/api/config/"
    # try:
    #     headers = {"Authorization": f"Bearer {token}"}
    #     response = requests.put(url, headers=headers, json=config_data, timeout=10)
    #     if response.status_code == 200:
    #         get_system_config.clear() # Clear cache
    #         return response.json(), None
    #     else:
    #         return None, _parse_error(response)
    # except requests.exceptions.RequestException as e:
    #     return None, _handle_request_exception(e, operation)
    # except Exception as e:
    #     logging.error(f"Unexpected error during {operation}: {str(e)}")
    #     return None, {'status': None, 'detail': f"An unexpected error occurred during {operation}.", 'raw_text': str(e)}
    logging.info(f"{operation}: Placeholder function called with data: {config_data}. Clearing cache and returning input data.")
    get_system_config.clear() # Simulate cache clearing
    return config_data, None # Simulate success by returning the input

# --- Employee App Specific (Moved from employee_app.py) ---

def create_interview_session(token, employee_id: int, exit_date: Optional[str], title: str = None):
    """Create an interview session. Returns (interview_dict, None) or (None, error_details)."""
    operation = f"creating interview session for employee {employee_id}"
    try:
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "employee_id": employee_id,
            "title": title or f"Exit Interview for Employee {employee_id}",
            "exit_date": exit_date, # Pass exit_date (can be None)
            # Assuming status defaults to SCHEDULED or similar in backend
            # Backend logic now starts it IN_PROGRESS and adds message
        }
        response = requests.post(
            f"{API_URL}/api/interviews/", 
            headers=headers, 
            json=payload, 
            timeout=15
        )
        if response.status_code == 201: # Created
            return response.json(), None
        else:
            return None, _parse_error(response)
    except requests.exceptions.RequestException as e:
        return None, _handle_request_exception(e, operation)
    except Exception as e:
        logging.error(f"Unexpected error during {operation}: {str(e)}")
        return None, {'status': None, 'detail': f"An unexpected error occurred during {operation}.", 'raw_text': str(e)}

def send_interview_message(token, interview_id: int, message: str, question_id: Optional[int] = None):
    """Send message during interview. Returns (response_dict, None) or (None, error_details)."""
    operation = f"sending message to interview {interview_id}"
    try:
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "content": message,
            "question_id": question_id
        }
        # Endpoint might be POST /interviews/{id}/messages or similar
        # Check the actual endpoint definition
        response = requests.post(
            f"{API_URL}/api/interviews/{interview_id}/messages", 
            headers=headers, 
            json=payload, 
            timeout=30 # Allow longer timeout for potential LLM processing
        )
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, _parse_error(response)
    except requests.exceptions.RequestException as e:
        return None, _handle_request_exception(e, operation)
    except Exception as e:
        logging.error(f"Unexpected error during {operation}: {str(e)}")
        return None, {'status': None, 'detail': f"An unexpected error occurred during {operation}.", 'raw_text': str(e)} 