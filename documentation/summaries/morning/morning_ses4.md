---
title: Exit Interview Bot - Morning Session 4
category: Summary
created: 2025-05-01
last_updated: 2025-05-01
version: 1.0
---

# Morning Session 4 - Predefined Questions Implementation

## Session Goals

1. Complete backend implementation for predefined questions transition
2. Begin frontend integration for structured interview flow
3. Develop initial test cases for the new implementation

## Part 1: Session Strategy (30 minutes)

### Context Review
- The app is transitioning from LLM-based conversations to structured predefined questions
- This will improve stability and reduce dependency on Groq API
- Backend structure has been created, but key endpoints need updating
- Frontend needs to be enhanced to show progress and handle question flow

### Today's Approach
- Focus on implementing core backend functionality first
- Then improve employee frontend flow
- Create basic tests to verify implementation
- Prioritize stability and error handling throughout

## Part 2: Backend Implementation (2 hours)

### Task 1: Update `create_interview` Endpoint
- Modify `create_interview` endpoint to use the first predefined question
- Update the model to store the initial question as first response
- Add error handling for missing questions
- Test the endpoint manually to confirm it returns the first question

```python
# Endpoint implementation for create_interview
@router.post("/interviews", response_model=InterviewSchema)
async def create_interview(
    employee: EmployeeCreate,
    db: Session = Depends(get_db)
):
    try:
        # Create the interview
        interview_id = crud.create_interview(
            db=db,
            employee_email=employee.email,
            employee_name=employee.name,
            exit_date=employee.exit_date
        )
        
        # Get the first question
        first_question = interview_questions.get_question_by_order(1)
        if not first_question:
            raise HTTPException(
                status_code=500, 
                detail="Failed to retrieve initial question"
            )
        
        # Store the initial bot message
        crud.create_response(
            db=db,
            interview_id=interview_id,
            employee_message=None,
            bot_response=first_question["text"],
            question_id=first_question["id"]
        )
        
        # Get the updated interview
        interview = crud.get_interview(db, interview_id)
        
        return interview
    except Exception as e:
        # Log the error
        logger.error(f"Error creating interview: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create interview"
        )
```

### Task 2: Update `send_message` Endpoint
- Implement question progression logic based on response count
- Handle the end-of-interview condition
- Add completion marker for finished interviews
- Enhance error handling for all operations

```python
@router.post("/{interview_id}/messages", response_model=MessageSchema)
async def send_message(
    interview_id: int,
    message: MessageCreate,
    db: Session = Depends(get_db)
):
    try:
        # Verify interview exists
        interview = crud.get_interview(db, interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        # Check if interview is already completed
        if interview.status == "COMPLETED":
            return {
                "content": "This interview has already been completed. Thank you for your participation.",
                "is_complete": True
            }
        
        # Get previous responses to determine next question
        previous_responses = crud.get_responses_by_interview(db, interview_id)
        next_question_order = len(previous_responses) + 1
        
        # Get next question
        next_question = interview_questions.get_question_by_order(next_question_order)
        
        # Store user's response
        response_id = crud.create_response(
            db=db,
            interview_id=interview_id,
            employee_message=message.content,
            bot_response=next_question["text"] if next_question else "Thank you for completing the interview.",
            question_id=next_question["id"] if next_question else None
        )
        
        # If no more questions, mark interview as complete
        if not next_question:
            crud.update_interview(
                db=db,
                interview_id=interview_id,
                update_dict={
                    "status": "COMPLETED", 
                    "completed_at": datetime.now()
                }
            )
            
        # Return response
        return {
            "id": response_id,
            "content": next_question["text"] if next_question else "Thank you for completing the exit interview. Your feedback is valuable to us.",
            "is_complete": next_question is None,
            "question_number": next_question_order if next_question else None,
            "total_questions": interview_questions.get_question_count()
        }
    except Exception as e:
        # Log the error
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process message"
        )
```

### Task 3: Implement Interview Questions Helper
- Create helper functions to manage predefined questions
- Implement methods to get questions by order
- Add utility to get total question count
- Ensure all question access is error-resistant

```python
# In interview_questions.py
from typing import Dict, List, Optional

# Predefined questions list
INTERVIEW_QUESTIONS = [
    {
        "id": 1,
        "text": "Why have you decided to leave the company?",
        "category": "Reasons"
    },
    {
        "id": 2,
        "text": "How would you describe the company culture?",
        "category": "Culture"
    },
    # Add more questions here...
]

def get_question_by_order(order: int) -> Optional[Dict]:
    """
    Get a question by its order in the sequence.
    
    Args:
        order: The position of the question (1-based index)
        
    Returns:
        The question dict or None if not found
    """
    if order < 1 or order > len(INTERVIEW_QUESTIONS):
        return None
    
    return INTERVIEW_QUESTIONS[order - 1]

def get_question_by_id(question_id: int) -> Optional[Dict]:
    """
    Get a question by its ID.
    
    Args:
        question_id: The unique ID of the question
        
    Returns:
        The question dict or None if not found
    """
    for question in INTERVIEW_QUESTIONS:
        if question["id"] == question_id:
            return question
    return None

def get_question_count() -> int:
    """
    Get the total number of questions.
    
    Returns:
        The number of questions in the predefined list
    """
    return len(INTERVIEW_QUESTIONS)

def get_all_questions() -> List[Dict]:
    """
    Get all predefined questions.
    
    Returns:
        The list of all questions
    """
    return INTERVIEW_QUESTIONS
```

## Part 3: Frontend Implementation (2 hours)

### Task 1: Update Employee App Interview UI
- Add progress indicator for interview completion
- Enhance interface to show question number and total
- Add clear completion state with visual feedback
- Improve error handling for API failures

```python
def _display_interview_interface():
    """Display the interview chat interface with progress tracking"""
    
    # Display messages
    if st.session_state.messages:
        for i, message in enumerate(st.session_state.messages):
            role = message.get("role", "")
            content = message.get("content", "")
            
            if role == "user":
                st.chat_message("user").write(content)
            elif role == "assistant":
                st.chat_message("assistant").write(content)
    
    # Check for interview completion
    if st.session_state.get("interview_complete", False):
        st.success("Thank you for completing your exit interview!")
        st.balloons()
        st.button("Return to Home", on_click=_reset_session)
    else:
        # Calculate progress
        user_messages = len([m for m in st.session_state.get("messages", []) 
                          if m.get("role") == "user"])
        
        # Get total questions if available
        total_questions = st.session_state.get("total_questions", 20)
        
        # Show progress bar and indicator
        if user_messages > 0:
            progress = min(1.0, user_messages / total_questions)
            st.progress(progress)
            st.caption(f"Question {user_messages + 1} of {total_questions}")
        
        # Message input
        user_input = st.chat_input("Your response:", key="user_input")
        
        if user_input:
            # Add user message to state
            st.session_state.messages.append({
                "role": "user", 
                "content": user_input
            })
            
            # Send to API
            with st.spinner("Processing..."):
                response, error = send_interview_message(
                    st.session_state.token,
                    st.session_state.interview_id,
                    user_input
                )
            
            if error:
                _display_api_error(error)
            elif response:
                # Add bot response
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response.get("content", "")
                })
                
                # Update question tracking info
                st.session_state.question_number = response.get("question_number")
                st.session_state.total_questions = response.get("total_questions")
                
                # Check if interview is complete
                if response.get("is_complete", False):
                    st.session_state.interview_complete = True
            
            # Refresh UI
            st.rerun()
```

### Task 2: Enhance API Client Functions
- Update client functions to work with new endpoint responses
- Add metadata extraction for question progress
- Improve error handling and recovery
- Add retries for transient failures

```python
def send_interview_message(token, interview_id, message):
    """
    Send a message to the interview API with improved error handling
    
    Returns:
        tuple: (response_data, error)
    """
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/interviews/{interview_id}/messages",
            json={"content": message},
            headers={"Authorization": f"Bearer {token}"},
            timeout=10  # Add timeout
        )
        
        # Handle different status codes
        if response.status_code == 200:
            return response.json(), None
        elif response.status_code == 429:
            return None, "The server is experiencing high load. Please try again in a moment."
        elif response.status_code == 404:
            return None, "Interview session not found. Please restart the interview."
        else:
            logging.error(f"API error: {response.status_code} - {response.text}")
            return None, f"Error communicating with server: {response.status_code}"
            
    except requests.exceptions.Timeout:
        return None, "Request timed out. Please try again."
    except requests.exceptions.ConnectionError:
        return None, "Connection error. Please check your internet connection."
    except Exception as e:
        logging.error(f"Unexpected error in send_interview_message: {str(e)}")
        return None, f"An unexpected error occurred: {str(e)}"
```

### Task 3: Improve Error Display
- Create consistent error display component
- Add user-friendly error messages
- Implement retry functionality for transient errors
- Ensure session state is preserved during errors

```python
def _display_api_error(error_message):
    """Display API errors with retry options for certain errors"""
    
    # Create error container
    error_container = st.container()
    
    with error_container:
        st.error(f"Error: {error_message}")
        
        # Different actions based on error type
        if "high load" in error_message or "timed out" in error_message:
            st.info("This appears to be a temporary issue. You can try again.")
            if st.button("Retry"):
                # Get last user message
                if st.session_state.get("messages"):
                    last_user_messages = [m for m in st.session_state.messages 
                                        if m.get("role") == "user"]
                    if last_user_messages:
                        last_message = last_user_messages[-1].get("content")
                        # Retry sending the last message
                        response, error = send_interview_message(
                            st.session_state.token,
                            st.session_state.interview_id,
                            last_message
                        )
                        if not error:
                            # Remove error and continue
                            st.session_state.messages.append({
                                "role": "assistant",
                                "content": response.get("content", "")
                            })
                            st.rerun()
                            
        elif "session not found" in error_message or "restart" in error_message:
            if st.button("Restart Interview"):
                _reset_session()
                st.rerun()
        else:
            # Generic error with report option
            st.button("Back to Home", on_click=_reset_session)
```

## Part 4: Testing (1 hour)

### Task 1: Backend Tests
- Create unit tests for question retrieval functions
- Test the interview creation and progression logic
- Verify error handling in API endpoints

```python
# Test example for question retrieval
def test_get_question_by_order():
    # Test valid question retrieval
    question = interview_questions.get_question_by_order(1)
    assert question is not None
    assert question["id"] == 1
    
    # Test out of range
    question = interview_questions.get_question_by_order(999)
    assert question is None
    
    # Test invalid input
    question = interview_questions.get_question_by_order(-1)
    assert question is None

# Test progression through questions
def test_interview_progression(test_client, test_db):
    # Create a test interview
    response = test_client.post(
        "/api/interviews",
        json={"email": "test@example.com", "name": "Test User", "exit_date": "2023-10-30"}
    )
    assert response.status_code == 200
    interview_data = response.json()
    interview_id = interview_data["id"]
    
    # Verify first question is provided
    responses = test_db.query(Response).filter_by(interview_id=interview_id).all()
    assert len(responses) == 1
    
    # Send messages and verify progression
    total_questions = interview_questions.get_question_count()
    
    for i in range(1, total_questions):
        response = test_client.post(
            f"/api/interviews/{interview_id}/messages",
            json={"content": f"Test answer {i}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check we're getting the right question number
        if i < total_questions - 1:
            assert data["is_complete"] is False
            assert data["question_number"] == i + 1
        else:
            # Last question
            assert data["is_complete"] is True
```

### Task 2: Manual Testing Checklist
- Create new interview and verify first question appears
- Answer questions and check progression
- Verify completion state when all questions are answered
- Test error handling for various scenarios
- Check frontend state preservation during page refreshes

## Part 5: Session Review and Next Steps (30 minutes)

### Completed Tasks
- Updated backend API endpoints for predefined questions
- Enhanced frontend to show progress and handle question flow
- Implemented error handling improvements
- Created test cases for verification

### Next Steps
1. Complete any remaining frontend integration
2. Expand test coverage for edge cases
3. Deploy changes to staging environment for validation
4. Document the implementation for other team members

### Known Issues to Address Next
- State management during browser refresh needs further testing
- Error handling for database connection failures
- Potential race conditions in concurrent updates

## Conclusion

This morning session implements the core functionality for the predefined questions transition. By focusing on the backend implementation first, we've created a solid foundation that the frontend can build upon. The enhanced error handling will improve stability, and the progress tracking will improve the user experience.

The implementation follows a staged approach to minimize disruption to the existing system while adding the new functionality. Each component has been designed to fail gracefully and preserve user state whenever possible.

---

*Last updated: 2025-05-01* 