import json
from datetime import datetime, date
import requests
import streamlit as st

# API connection settings
API_URL = "http://localhost:8000"

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

# Initialize session state
if "token" not in st.session_state:
    st.session_state.token = None
if "interview_id" not in st.session_state:
    st.session_state.interview_id = None
if "current_question" not in st.session_state:
    st.session_state.current_question = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "interview_complete" not in st.session_state:
    st.session_state.interview_complete = False

# Authentication function
def get_access_token(email, full_name, department, exit_date=None):
    """Get access token for employee"""
    try:
        response = requests.post(
            f"{API_URL}/api/auth/employee-access",
            json={
                "email": email,
                "full_name": full_name,
                "department": department,
                "exit_date": exit_date
            }
        )
        if response.status_code == 200:
            return response.json()["access_token"]
        else:
            st.error(f"Error getting access token: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error connecting to server: {str(e)}")
        return None

# Start interview function
def start_interview(token, employee_id, exit_date=None):
    """Start a new exit interview"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        exit_date_str = exit_date.isoformat() if exit_date else None
        
        response = requests.post(
            f"{API_URL}/api/interviews/start",
            headers=headers,
            json={
                "employee_id": employee_id,
                "exit_date": exit_date_str
            }
        )
        
        if response.status_code == 200:
            return response.json()["id"]
        else:
            st.error(f"Error starting interview: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error connecting to server: {str(e)}")
        return None

# Send message function
def send_message(token, interview_id, message, question_id=None):
    """Send a message to the interview API"""
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        response = requests.post(
            f"{API_URL}/api/interviews/{interview_id}/message",
            headers=headers,
            json={
                "interview_id": interview_id,
                "message": message,
                "question_id": question_id
            }
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error sending message: {response.text}")
            return None
    except Exception as e:
        st.error(f"Error connecting to server: {str(e)}")
        return None

# Login tab if not authenticated
if not st.session_state.token:
    st.subheader("Welcome to your exit interview")
    st.write("""
    Thank you for taking the time to participate in this exit interview.
    Your feedback is valuable and will help us improve our workplace.
    
    This conversation is confidential and will be used to understand your experience better.
    """)
    
    with st.form("login_form"):
        email = st.text_input("Email", placeholder="your.email@company.com")
        full_name = st.text_input("Full Name", placeholder="John Doe")
        department = st.text_input("Department", placeholder="Engineering")
        exit_date = st.date_input("Last Day at Company", min_value=date.today())
        
        submit = st.form_submit_button("Start Interview")
        
        if submit:
            if not email or not full_name:
                st.error("Please provide your email and full name")
            else:
                # Get token
                token = get_access_token(email, full_name, department, exit_date.isoformat())
                if token:
                    st.session_state.token = token
                    # Start interview
                    interview_id = start_interview(token, 1)  # ID will be determined by API
                    if interview_id:
                        st.session_state.interview_id = interview_id
                        st.success("Interview started successfully!")
                        st.rerun()

# Interview interface if authenticated
else:
    # Display chat messages
    if st.session_state.messages:
        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f'<div class="chat-message user-message"><b>You:</b> {message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-message bot-message"><b>ExitBot:</b> {message["content"]}</div>', unsafe_allow_html=True)
    
    # Display current question or completion message
    if st.session_state.interview_complete:
        st.success("Thank you for completing your exit interview!")
        st.balloons()
        
        if st.button("Start a New Interview"):
            # Reset session state
            st.session_state.token = None
            st.session_state.interview_id = None
            st.session_state.current_question = None
            st.session_state.messages = []
            st.session_state.interview_complete = False
            st.rerun()
    else:
        # Message input
        with st.form("message_form", clear_on_submit=True):
            # Determine which question to show
            if not st.session_state.current_question and not st.session_state.messages:
                # First message - get current question from API
                placeholder = "The interview will begin once you send your first message..."
            else:
                placeholder = "Type your response here..."
                
            message = st.text_area("Your response:", placeholder=placeholder, height=100)
            submitted = st.form_submit_button("Send")
            
            if submitted and message:
                # Add user message to chat
                st.session_state.messages.append({"role": "user", "content": message})
                
                # Send to API
                question_id = st.session_state.current_question["id"] if st.session_state.current_question else None
                response = send_message(
                    st.session_state.token,
                    st.session_state.interview_id,
                    message,
                    question_id
                )
                
                if response:
                    # Add bot response to chat
                    st.session_state.messages.append({"role": "assistant", "content": response["response"]})
                    
                    # Update current question
                    st.session_state.current_question = response["current_question"]
                    
                    # Check if interview is complete
                    if response["is_complete"]:
                        st.session_state.interview_complete = True
                
                st.rerun()

# Footer
st.markdown("""
<div class="centered">
<small>ExitBot - HR Exit Interview Bot © 2025</small>
</div>
""", unsafe_allow_html=True) 