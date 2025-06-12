import streamlit as st
import os
import logging
import time
import random

# import json
# from datetime import datetime, date, timedelta

# Import API client functions
from exitbot.frontend.api_client import (
    get_employee_access_details,
    create_interview_session,
    send_interview_message,
    # We might need a way to display errors similarly to hr_app
    # Let's reuse the error parsing/logging helpers for now, but display directly
    # _parse_error,
    # _handle_request_exception,
)

# Import design system and components
from exitbot.frontend.components.design_system import get_base_css, get_employee_app_css, get_theme_css
from exitbot.frontend.components.welcome import render_welcome, render_completion
from exitbot.frontend.components.chat_interface import render_chat_interface, create_typing_effect

# API connection settings - Read from environment variable
API_URL = os.getenv("API_URL", "http://localhost:8000")

# Page configuration
st.set_page_config(
    page_title="ExitBot - Exit Interview",
    page_icon="👋",
    layout="centered",
    initial_sidebar_state="collapsed",  # Start with collapsed sidebar for clean interface
)

# Apply custom styling from the design system
st.markdown(
    get_base_css() + get_employee_app_css(),
    unsafe_allow_html=True,
)

# Initialize session state concisely
def initialize_session_state():
    """Initialize session state with default values for personalization."""
    if "interview_data" not in st.session_state:
        st.session_state.interview_data = {}
        
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    if "user_theme_preference" not in st.session_state:
        st.session_state.user_theme_preference = "default"
        
    if "accessibility_options" not in st.session_state:
        st.session_state.accessibility_options = {
            "reduced_motion": False,
            "high_contrast": False,
            "large_text": False
        }

    defaults = {
        "token": None,
        "employee_id": None,
        "interview_id": None,
        "current_question": None,
        "interview_complete": False,
        "interview_details": None,
        "welcome_complete": False,
        "thinking": False,  # For typing animation
        "question_number": 0,
        "total_questions": 0,
        "employee_name": "",
        "company_name": "ExitBot",
    }
    for key, default_value in defaults.items():
        st.session_state.setdefault(key, default_value)


initialize_session_state()


# --- Helper Functions ---
def display_api_error(error_details, context="Error"):
    """Display API error messages using Streamlit components."""
    if error_details:
        message = error_details.get("detail", "An unknown error occurred.")
        logging.warning(f"{context}: {message} (Raw: {error_details.get('raw_text')})")
        st.error(f"{context}: {message}")
    else:
        logging.error("display_api_error called with None or empty error_details")
        st.error(
            "An unexpected error occurred while trying to process your request."
        )


def _handle_login_form():
    """Handle employee token submission and verification"""
    st.markdown(
        """
        <h1>Exit Interview Portal</h1>
        <p class="subtitle">Please enter your access token to begin your exit interview.</p>
        """, 
        unsafe_allow_html=True
    )
    
    # Create a form for token input
    with st.form("access_token_form"):
        token = st.text_input(
            "Access Token",
            placeholder="Enter your access token",
            help="This token was provided to you in your exit interview email."
        )
        
        submitted = st.form_submit_button("Start Interview")
        
        if submitted:
            if not token or len(token.strip()) < 8:  # Simple validation
                st.error("Please enter a valid access token.")
                return
            
            # Show loading state
            with st.spinner("Verifying access token..."):
                # Call API to validate token
                employee_details, error = get_employee_access_details(token)

                if error:
                    display_api_error(error, "Access verification failed")
                    return
                
                if employee_details:
                    # Store token and employee details
                        st.session_state.token = token
                    st.session_state.employee_id = employee_details.get("employee_id")
                    st.session_state.employee_name = employee_details.get("name", "")
                    st.session_state.company_name = employee_details.get("company", "ExitBot")
                    
                    # Check if interview already exists
                    if employee_details.get("interview_id"):
                        st.session_state.interview_id = employee_details.get("interview_id")
                        st.session_state.interview_complete = employee_details.get("is_complete", False)
                        
                        # If complete, we'll show the completion screen
                        if st.session_state.interview_complete:
                            st.success("Your completed interview has been loaded.")
                        else:
                            st.success("Your in-progress interview has been loaded.")
                    
                    # Rerun to show the appropriate screen
                    st.rerun()
                else:
                    st.error("Invalid access token. Please check and try again.")


def _start_interview_callback():
    """Callback function for the welcome screen's start button"""
    
    # Mark the welcome as complete so we don't show it again
    st.session_state.welcome_complete = True
    
    # If we don't have an interview yet, create one
    if not st.session_state.interview_id:
        with st.spinner("Starting your interview..."):
            # Create interview session
            result, error = create_interview_session(st.session_state.token)
            
            if error:
                display_api_error(error, "Failed to start interview")
                # Reset welcome complete so user can try again
                st.session_state.welcome_complete = False
                return
            
            if result:
                st.session_state.interview_id = result.get("interview_id")
                st.session_state.messages = result.get("messages", [])
                st.session_state.current_question = result.get("current_question")
                
                # Set question tracking numbers
                st.session_state.question_number = 1
                st.session_state.total_questions = result.get("total_questions", 10)
                
                # Success message with animation will be shown on rerun
                st.rerun()
            else:
                st.error("Failed to start interview session. Please try again.")
                # Reset welcome complete so user can try again
                st.session_state.welcome_complete = False


def _handle_message_submission(message_content):
    """Handle message submission from chat interface"""
    
    if not message_content or not message_content.strip():
        # Don't process empty messages
        return
    
    # Set thinking state to show animation
    st.session_state.thinking = True
    
    # Add user message to local state immediately for UI update
    st.session_state.messages.append({
        "role": "user",
        "content": message_content
    })
    
    # Send message to API
    result, error = send_interview_message(
        st.session_state.token,
        st.session_state.interview_id,
        message_content
    )
    
    if error:
        display_api_error(error, "Failed to send message")
        # Remove the user message we added if it failed
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
            st.session_state.messages.pop()
        st.session_state.thinking = False
        return
    
    if result:
        # Update session state with new information
        bot_message = result.get("bot_message", "")
        
        # Set thinking to false now that we have a response
        st.session_state.thinking = False
        
        # Add bot message to local state
        st.session_state.messages.append({
            "role": "assistant",
            "content": bot_message
        })
        
        # Update interview state
        st.session_state.current_question = result.get("current_question")
        st.session_state.interview_complete = result.get("is_complete", False)
        
        # Update question tracking
        if result.get("is_complete", False):
            st.session_state.question_number = st.session_state.total_questions
        else:
            st.session_state.question_number += 1
            
        # Force a rerun to update the UI
        st.rerun()
    else:
        st.error("Failed to process your response. Please try again.")
        st.session_state.thinking = False


def _display_interview_interface():
    """Display the enhanced chat interface for the ongoing interview"""
    
    # If interview is complete, show completion screen
    if st.session_state.interview_complete:
        render_completion(
            st.session_state.employee_name,
            st.session_state.company_name
        )
        return
    
    # Main interview interface
        st.markdown(
        f"""
        <h1>Your Exit Interview</h1>
        <p class="subtitle">Please answer the following questions honestly and thoroughly.</p>
        """, 
        unsafe_allow_html=True
    )
    
    # Use our enhanced chat interface component
    render_chat_interface(
        messages=st.session_state.messages,
        on_message_submit=_handle_message_submission,
        current_question_number=st.session_state.question_number,
        total_questions=st.session_state.total_questions,
        is_complete=st.session_state.interview_complete,
        is_thinking=st.session_state.thinking
    )


def apply_personalization():
    """Apply user theme and accessibility preferences."""
    # Apply theme
    if st.session_state.user_theme_preference and st.session_state.user_theme_preference != "default":
        theme_css = get_theme_css(st.session_state.user_theme_preference)
        st.markdown(theme_css, unsafe_allow_html=True)
    
    # Apply accessibility options
    if st.session_state.accessibility_options:
        options = st.session_state.accessibility_options
        
        if options.get("reduced_motion", False):
        st.markdown(
            """
                <style>
                * {
                    animation-duration: 0.001s !important;
                    transition-duration: 0.001s !important;
                    scroll-behavior: auto !important;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            
        if options.get("high_contrast", False):
            st.markdown(
                """
                <style>
                body, [class*="st-"] {
                    background-color: #000000 !important;
                    color: #FFFFFF !important;
                }
                
                .chat-message, .chat-interface-header, .completion-container {
                    background-color: #222222 !important;
                    border: 2px solid #FFFFFF !important;
                }
                
                .stButton > button {
                    background-color: #FFFFFF !important;
                    color: #000000 !important;
                    border: 2px solid #FFFFFF !important;
                }
                
                a {
                    color: #3B82F6 !important;
                    text-decoration: underline !important;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            
        if options.get("large_text", False):
                st.markdown(
                """
                <style>
                html {
                    font-size: 1.25rem !important;
                }
                </style>
                """,
                unsafe_allow_html=True
            )


def personalize_for_employee(employee_data):
    """Set personalized options based on employee data."""
    # In a real app, we might pull personalization preferences from a database
    # For this demo, we'll set some defaults based on employee department
    department = employee_data.get("department", "").lower()
    
    # Example: Personalize by department
    if "design" in department or "creative" in department:
        st.session_state.user_theme_preference = "creative"
    elif "engineering" in department or "tech" in department:
        st.session_state.user_theme_preference = "tech"
    elif "finance" in department or "accounting" in department:
        st.session_state.user_theme_preference = "classic"
    
    # We could also personalize based on other factors like tenure, location, etc.
    

def render_interview_chat_interface():
    """Render the chat interface for the exit interview with personalization."""
    # Get interview data
    interview_id = st.session_state.interview_data.get("id")
    current_question = st.session_state.interview_data.get("current_question", 1)
    total_questions = st.session_state.interview_data.get("total_questions", 10)
    is_thinking = False
    
    # Display accessibility preferences in chat interface header
    with st.expander("Accessibility & Personalization", expanded=False):
        st.markdown("### Customize Your Experience")
        
        # Theme selection
        theme_options = {
            "default": "Default Theme", 
            "creative": "Creative Theme", 
            "tech": "Tech Theme", 
            "classic": "Classic Theme"
        }
        
        selected_theme = st.selectbox(
            "Select Theme",
            options=list(theme_options.keys()),
            format_func=lambda x: theme_options[x],
            index=list(theme_options.keys()).index(st.session_state.user_theme_preference)
        )
        
        if selected_theme != st.session_state.user_theme_preference:
            st.session_state.user_theme_preference = selected_theme
            st.rerun()
        
        # Accessibility options
        acc_col1, acc_col2 = st.columns(2)
        
        with acc_col1:
            reduced_motion = st.checkbox(
                "Reduce Animations",
                value=st.session_state.accessibility_options.get("reduced_motion", False),
                help="Minimize animations for reduced motion sensitivity"
            )
            
            if reduced_motion != st.session_state.accessibility_options.get("reduced_motion", False):
                st.session_state.accessibility_options["reduced_motion"] = reduced_motion
                st.rerun()
        
        with acc_col2:
            high_contrast = st.checkbox(
                "High Contrast",
                value=st.session_state.accessibility_options.get("high_contrast", False),
                help="Increase contrast for better visibility"
            )
            
            if high_contrast != st.session_state.accessibility_options.get("high_contrast", False):
                st.session_state.accessibility_options["high_contrast"] = high_contrast
                st.rerun()
        
        # Text size option
        large_text = st.checkbox(
            "Larger Text Size",
            value=st.session_state.accessibility_options.get("large_text", False),
            help="Increase text size for better readability"
        )
        
        if large_text != st.session_state.accessibility_options.get("large_text", False):
            st.session_state.accessibility_options["large_text"] = large_text
            st.rerun()

        st.markdown("---")
        st.markdown(
            """
            <div class="personalization-note">
                Your preferences will be saved for future sessions.
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Determine user's department and tenure for personalization
    department = st.session_state.interview_data.get("department", "")
    tenure_years = st.session_state.interview_data.get("tenure_years", 0)
    
    # Add personalized elements based on department and tenure
    if department and tenure_years:
        st.markdown(
            f"""
            <div class="personalization-banner">
                <div class="personalization-icon">👋</div>
                <div class="personalization-content">
                    <div class="personalization-title">Personalized for {st.session_state.employee_name}</div>
                    <div class="personalization-text">
                        Thank you for your {tenure_years} {'years' if tenure_years > 1 else 'year'} with our {department} team!
                        We've customized this interview to focus on your specific experience.
                    </div>
                </div>
        </div>
        """,
            unsafe_allow_html=True
        )
    
    # Run the chat interface with progress indicator
    render_chat_interface(
        st.session_state.messages,
        lambda msg: on_message_submit(msg, interview_id),
        current_question,
        total_questions,
        is_complete=False,
        is_thinking=is_thinking
    )


def on_message_submit(message, interview_id):
    """Handle message submission with personalized response generation."""
    if not message.strip():
        return
    
    # Add user message to chat
    st.session_state.messages.append({"role": "user", "content": message})
    
    # In a real app, we'd send the message to the API
    # For demo, we'll simulate a response
    
    # Show thinking indicator
    with st.spinner("Processing your response..."):
        time.sleep(1)  # Simulate API call
    
        # Generate a personalized response based on the user's department
        department = st.session_state.interview_data.get("department", "").lower()
        
        # Personalize the follow-up questions based on department/role
        if "engineering" in department or "development" in department:
            follow_ups = [
                "How would you rate the technical challenges in your role?",
                "Did you have access to the tools and resources you needed?",
                "How was the code review process in your team?"
            ]
        elif "sales" in department or "marketing" in department:
            follow_ups = [
                "How would you describe the sales targets and quotas?",
                "Did you receive adequate marketing support and materials?",
                "How was your relationship with the product team?"
            ]
        elif "hr" in department or "human resources" in department:
            follow_ups = [
                "How would you describe the company's culture and values?",
                "Did you have the tools you needed to support employees?",
                "What aspects of our HR policies could be improved?"
            ]
        else:
            follow_ups = [
                "What aspects of your role did you find most challenging?",
                "Did you have the resources you needed to succeed?",
                "How would you describe the team dynamics?"
            ]
        
        # Get a random follow-up
        follow_up = random.choice(follow_ups)
        
        # Create a personalized response
        response = f"Thank you for sharing that feedback about your experience. {follow_up}"
        
        # Add system response to chat
        st.session_state.messages.append({"role": "system", "content": response})
        
        # Update current question (in a real app, this would come from the API)
        current_question = st.session_state.interview_data.get("current_question", 1)
        st.session_state.interview_data["current_question"] = current_question + 1
        
        # Check if interview is complete
        if current_question + 1 > st.session_state.interview_data.get("total_questions", 10):
            st.session_state.interview_data["is_complete"] = True
            
            # In a real app, we'd update the API
            # For demo, we'll just update the session state
            st.rerun()
            

def main():
    """Main entry point for the employee exit interview application."""
    # Set page config
    st.set_page_config(
        page_title="Exit Interview | ExitBot",
        page_icon="📊",
        layout="centered"
    )
    
    # Initialize global session state
    initialize_session_state()
    
    # Get cookie manager
    cookies = stx.CookieManager()
    
    # Apply theme and accessibility preferences
    apply_personalization()
    
    # -- CSS Injection --
    st.markdown(get_base_css(), unsafe_allow_html=True)
    st.markdown(get_employee_app_css(), unsafe_allow_html=True)
    
    # -- Handle authentication --
    # Check for token in cookie first (page reloads)
    if "token" not in st.session_state:
        st.session_state.token = cookies.get("auth_token")
        
    if not st.session_state.token:
        # User is not authenticated, show login
        if employee_login(login_employee, cookies):
            st.rerun()  # Reload after login
        return
    
    # -- Load interview data if not already loaded --
    if not st.session_state.interview_data:
        with st.spinner("Loading your interview..."):
            employee_data, error = get_employee_data(st.session_state.token)
            
            if error:
                st.error(f"Error loading interview: {error}")
                if st.button("Try Again"):
                    st.rerun()
                return
                
            if employee_data:
                st.session_state.interview_data = employee_data
                st.session_state.employee_name = employee_data.get("name", "Employee")
                st.session_state.company_name = employee_data.get("company_name", "Company")
                
                # Pre-load personalization based on employee data
                personalize_for_employee(employee_data)
    
    # -- Check if interview is complete --
    is_complete = st.session_state.interview_data.get("is_complete", False)
    
    # -- Render appropriate view --
    if is_complete:
        # Calculate stats for completion
        questions_answered = len([m for m in st.session_state.messages if m["role"] == "user"])
        
        # Calculate time spent (in a real app, this would come from the backend)
        time_spent = st.session_state.interview_data.get("duration", "15 min")
        
        # Render completion screen
        render_completion(
            st.session_state.employee_name,
            st.session_state.company_name,
            questions_answered,
            time_spent
        )
    else:
        # Check if we're showing welcome screen
        if "show_welcome" not in st.session_state:
            st.session_state.show_welcome = True
            
        if st.session_state.show_welcome:
            # Render welcome view
            render_welcome(
                st.session_state.employee_name,
                st.session_state.company_name,
                lambda: set_session_state("show_welcome", False)
            )
        else:
            # Render chat interface
            render_interview_chat_interface()


def set_session_state(key, value):
    """Helper function to set session state and rerun."""
    st.session_state[key] = value
    st.rerun()


# Run the app
if __name__ == "__main__":
    main()
