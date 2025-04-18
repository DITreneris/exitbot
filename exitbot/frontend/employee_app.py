import json
from datetime import datetime, date, timedelta
# import requests # No longer needed directly
import streamlit as st
import os
import logging # Import logging

# Import API client functions
from exitbot.frontend.api_client import (
    get_employee_access_details,
    create_interview_session,
    send_interview_message,
    # We might need a way to display errors similarly to hr_app
    # Let's reuse the error parsing/logging helpers for now, but display directly
    _parse_error, 
    _handle_request_exception 
)

# API connection settings - Read from environment variable
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Page configuration
st.set_page_config(
    page_title="ExitBot - Exit Interview",
    page_icon="👋",
    layout="centered",
)

# Custom styling
st.markdown("""
<style>
div.stButton > button {
    width: 100%;
}
.chat-message {
    padding: 10px;
    border-radius: 10px;
    margin-bottom: 10px;
}
.user-message {
    background-color: #e6f7ff;
    border: 1px solid #91d5ff;
}
.bot-message {
    background-color: #f6ffed;
    border: 1px solid #b7eb8f;
}
.centered {
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# App title
st.title("👋 ExitBot Exit Interview")

# Initialize session state more concisely
def initialize_session_state():
    defaults = {
        "token": None,
        "employee_id": None,
        "interview_id": None,
        "current_question": None,
        "messages": [],
        "interview_complete": False,
        "interview_details": None
    }
    for key, default_value in defaults.items():
        st.session_state.setdefault(key, default_value)

initialize_session_state()

# --- Helper Functions ---
def display_api_error(error_details, context="Error"):
    """Display API error messages using Streamlit components (similar to hr_app)."""
    if error_details:
        message = error_details.get('detail', "An unknown error occurred.")
        # Log the raw details using the imported logging
        logging.warning(f"{context}: {message} (Raw: {error_details.get('raw_text')})") 
        st.error(f"{context}: {message}")
    else:
        logging.error("display_api_error called with None or empty error_details")
        st.error("An unexpected UI error occurred while trying to display an API error.")

def _handle_login_form():
    """Displays and handles the employee login form."""
    st.subheader("Welcome to your exit interview")
    st.write("""
    Thank you for taking the time to participate in this exit interview.
    Your feedback is valuable and will help us improve our workplace.

    This conversation is confidential and will be used to understand your experience better.
    """)

    with st.form("login_form"):
        email = st.text_input("Email", placeholder="your.email@company.com")
        full_name = st.text_input("Full Name", placeholder="John Doe")
        # department = st.text_input("Department", placeholder="Engineering") # Removed
        # exit_date_input = st.date_input("Last Day at Company", min_value=date.today() - timedelta(days=365), max_value=date.today() + timedelta(days=365), value=date.today()) # Removed

        submit = st.form_submit_button("Start Interview")

        if submit:
            if not email or not full_name:
                st.error("Please provide your email and full name")
            else:
                # exit_date_str = exit_date_input.isoformat() # Removed
                # Call API client function - Removed department and exit_date
                # Add spinner
                with st.spinner("Verifying access..."):
                    access_details, error = get_employee_access_details(email, full_name)

                if error:
                    display_api_error(error, "Could not start interview")
                elif access_details:
                    token = access_details.get("access_token")
                    employee_id = access_details.get("employee_id")
                    
                    if token and employee_id:
                        st.session_state.token = token
                        st.session_state.employee_id = employee_id
                        
                        # Create interview session using API client
                        # Pass None for exit_date
                        with st.spinner("Initializing interview session..."):
                            interview_data, creation_error = create_interview_session(token, employee_id, exit_date=None)
                        
                        if creation_error:
                            display_api_error(creation_error, "Failed to create interview session")
                            # Reset token/id if session creation fails
                            st.session_state.token = None
                            st.session_state.employee_id = None
                        elif interview_data:
                            st.session_state.interview_id = interview_data.get("id")
                            st.session_state.interview_details = interview_data # Store details
                            
                            # Check for interview_id before proceeding
                            if not st.session_state.interview_id:
                                logging.error(f"API Error: create_interview_session response missing 'id'. Response: {interview_data}")
                                st.error("Interview session creation failed (missing ID).")
                                st.session_state.token = None # Reset auth state
                                st.session_state.employee_id = None
                                # No rerun here, stay on login page
                            else:
                                # --- Handle initial message from backend ---
                                initial_message = interview_data.get("initial_message")
                                if initial_message and initial_message.get("content"):
                                    st.session_state.messages.append({
                                        "role": "assistant", 
                                        "content": initial_message["content"]
                                    })
                                    st.session_state.current_question = initial_message 
                                    logging.info(f"Initial message for interview {st.session_state.interview_id} added to session state.")
                                else:
                                    # Log if message specifically is missing, not just content empty
                                    if initial_message is None:
                                         logging.warning(f"Interview {st.session_state.interview_id} created, but no 'initial_message' field received from backend. Response: {interview_data}")
                                    else: # Message field exists but content is empty/None
                                         logging.warning(f"Interview {st.session_state.interview_id} created, but initial_message content is empty. Message: {initial_message}")
                                    # Keep current_question as None, UI will show generic prompt
    
                                st.success("Interview started successfully!")
                                st.rerun() # Rerun to switch to interview view
                        else:
                             # Log the empty/unexpected response
                             logging.error(f"API Error: create_interview_session returned None or empty data. Error object: {creation_error}")
                             st.error("Interview session creation returned unexpected result.")
                             st.session_state.token = None
                             st.session_state.employee_id = None
                    else:
                        # Log the incomplete details
                        logging.error(f"API Error: get_employee_access_details response missing token or employee_id. Response: {access_details}")
                        st.error("Received incomplete access details from server.")
                else:
                     # Log the empty/unexpected response
                     logging.error(f"API Error: get_employee_access_details returned None or empty data. Error object: {error}")
                     st.error("Could not get access details (unexpected result).")

def _display_interview_interface():
    """Displays the main chat interface for the interview."""
    # Display chat messages
    if st.session_state.messages:
        for message in st.session_state.messages:
            role_label = "You" if message["role"] == "user" else "ExitBot"
            message_class = "user-message" if message["role"] == "user" else "bot-message"
            content = message.get("content", "*message content missing*")
            st.markdown(f'<div class="chat-message {message_class}"><b>{role_label}:</b> {content}</div>', unsafe_allow_html=True)

    # Display current question or completion message
    if st.session_state.interview_complete:
        st.success("Thank you for completing your exit interview!")
        st.balloons()

        if st.button("Start a New Interview"):
            # Reset session state completely
            for key in list(st.session_state.keys()):
                 del st.session_state[key]
            st.rerun()
    else:
        # --- Determine input placeholder ---
        # Use a consistent placeholder now that the redundant question prompt is removed
        input_placeholder = "Type your response here..."

        # Message input form
        with st.form("message_form", clear_on_submit=True):
            message = st.text_area("Your response:", placeholder=input_placeholder, height=100)
            submitted = st.form_submit_button("Send")

            if submitted and message:
                st.session_state.messages.append({"role": "user", "content": message})
                question_id = None

                with st.spinner("Sending message and waiting for response..."):
                    response_data, error = send_interview_message(
                        st.session_state.token,
                        st.session_state.interview_id,
                        message,
                        question_id
                    )

                    if error:
                        display_api_error(error, "Failed to send message or get response")
                    elif response_data:
                        if isinstance(response_data, dict) and response_data.get("content"):
                            assistant_message = {
                                "role": "assistant",
                                "content": response_data["content"]
                            }
                            st.session_state.messages.append(assistant_message)

                            concluding_text = "Thank you for completing the exit interview."
                            if response_data["content"].strip().startswith(concluding_text):
                                st.session_state.interview_complete = True
                                st.session_state.current_question = None
                                logging.info(f"Interview {st.session_state.interview_id} marked as complete by frontend.")
                            else:
                                st.session_state.current_question = response_data
                                st.session_state.interview_complete = False
                        else:
                             logging.error(f"API Error: Received unexpected response structure from send_message. Expected dict with 'content', got: {response_data}")
                             st.error("Received an unexpected response format from the server.")
                    else:
                        logging.error("API Error: Received no response data (None) from send_message.")
                        st.error("Received no response data from server.")

            elif submitted:
                 st.warning("Please enter a response.")

# --- API Functions (Removed - Using api_client now) ---
# [ Removed get_employee_access_details, create_interview_session, send_interview_message local definitions ]

# --- Main App Logic ---
def main():
    # App title is already set globally
    # Session state initialization is already done globally
    
    if not st.session_state.token:
        _handle_login_form()
    else:
        # Interview interface logic (chat display, input, etc.)
        _display_interview_interface()

    # Footer (Moved inside main)
    st.markdown("""
    <div class="centered">
    <small>ExitBot - HR Exit Interview Bot © 2025</small>
    </div>
    """, unsafe_allow_html=True) 

if __name__ == "__main__":
    main() 