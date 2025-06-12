---
title: Exit Interview Bot - Predefined Questions Technical Documentation
category: Technical
created: 2025-05-01
last_updated: 2025-05-01
version: 1.0
---

# Predefined Questions System: Technical Documentation

## Architecture Overview

The predefined questions system replaces the LLM-based conversation flow with a structured, deterministic sequence of questions. This document explains the technical implementation, components, and how to extend or modify the system.

## Core Components

### 1. Question Storage (`interview_questions.py`)

The predefined questions are stored in `exitbot/app/core/interview_questions.py` as a Python list of dictionaries. Each question contains:

- `id`: Unique identifier for the question
- `text`: The actual question text
- `category`: Category for grouping and analysis

The module provides several helper functions:

```python
# Get question by sequence order (1-based)
get_question_by_order(order: int) -> Optional[Dict]

# Get question by its ID
get_question_by_id(question_id: int) -> Optional[Dict]

# Get total question count
get_question_count() -> int

# Get all questions
get_all_questions() -> List[Dict]
```

### 2. Interview API Endpoints (`interview.py`)

The API endpoints in `exitbot/app/api/interview.py` handle the interview flow:

- `start_interview`: Creates a new interview and provides the first question
- `process_message`: Stores the user's response and returns the next question
- `complete_interview`: Marks an interview as complete
- `get_interview`: Retrieves interview details

### 3. Schemas (`interview.py` in schemas)

The `MessageSchema` class defines the response format for predefined questions:

```python
class MessageSchema(BaseModel):
    id: Optional[int] = Field(None, description="Response ID")
    content: str = Field(..., description="Message content/question text")
    is_complete: bool = Field(default=False, description="Whether this is the last question")
    question_number: Optional[int] = Field(None, description="Current question number")
    total_questions: Optional[int] = Field(None, description="Total number of questions")
```

### 4. Frontend Implementation (`employee_app.py`)

The frontend displays questions, tracks progress, and handles user responses:

- Progress indicator shows completion percentage
- Question counter (e.g., "Question 3 of 20")
- Error handling with retry options
- Completion celebration when all questions are answered

## Flow Logic

1. An interview is created via `start_interview`
2. The first question is automatically added as a bot response
3. The user submits an answer via `process_message`
4. The system:
   - Stores the user's response
   - Calculates the next question based on response count
   - Returns the next question or completion message
   - Updates progress information
5. When all questions are answered, the interview is marked complete

## Data Model

The system uses the existing database models:

- `Interview`: Stores interview metadata and status
- `Response`: Stores each question and answer pair

No schema changes are required for this implementation as it uses the existing data structures.

## Extension Points

### Adding or Modifying Questions

To add, remove, or modify questions:

1. Edit the `INTERVIEW_QUESTIONS` list in `interview_questions.py`
2. Ensure IDs are unique and sequential
3. Add appropriate categories for reporting
4. No additional code changes are required

Example:

```python
INTERVIEW_QUESTIONS = [
    # Existing questions...
    {"id": 21, "text": "What did you think of our company's sustainability practices?", "category": "Environment"},
    # More new questions...
]
```

### Conditional Questions

To implement conditional questions (questions that only appear based on previous answers):

1. Modify the `process_message` endpoint in `interview.py` to include logic for determining the next question
2. Create a new helper function in `interview_questions.py` to select questions based on conditions

Example implementation:

```python
def get_next_question(interview_id, previous_responses):
    """Get the next question based on previous responses"""
    # Add logic to determine next question
    # Example: Skip question 5 if question 3 was answered negatively
    # ...
```

### Adding Response Analysis

To analyze responses as they are submitted:

1. Add analysis logic in the `process_message` endpoint
2. Store analysis results in the Response model's `sentiment` field or metadata

## Performance Considerations

- The predefined questions approach has minimal CPU and memory requirements
- Database load is reduced as fewer operations are performed
- Response time is significantly improved without LLM API calls
- The system can be scaled horizontally with load balancing

## Testing

The system includes unit and integration tests:

- `test_predefined_questions.py`: Tests the core functionality
- `test_interview_flow.py`: Tests the end-to-end flow

To run tests:

```bash
pytest -xvs exitbot/tests/test_predefined_questions.py
```

## Monitoring

Important metrics to monitor:

- Interview completion rate (% of started interviews that are completed)
- Average time per question
- Error rates by question
- Total interviews processed per day/week

## Future Enhancements

Planned improvements to the system:

1. Question branching based on previous answers
2. Question randomization for certain categories
3. Support for conditional question skipping
4. Integration with analytics dashboard
5. Export functionality for question responses by category

## Related Documentation

- [Deployment Guide](../../guides/deployment/predefined_questions_deployment.md)
- [User Guide for HR Staff](../../guides/user/hr_predefined_questions.md)
- [API Documentation](../api/interview_endpoints.md) 