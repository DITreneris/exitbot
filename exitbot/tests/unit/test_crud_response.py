"""
Unit tests for response CRUD operations.
"""
# Remove unused pytest
# import pytest
# Remove unused Dict, Any
# from typing import Dict, Any

from sqlalchemy.orm import Session

from exitbot.app.db import crud

# Remove unused Response
# from exitbot.app.db.models import Response
# Remove unused ResponseCreate
# from exitbot.app.schemas.response import ResponseCreate


def test_create_response(test_db: Session, test_interview):
    """Test creating a new response successfully."""
    response_data = {
        "interview_id": test_interview.id,
        "question_id": 1,
        "employee_message": "This is my answer.",
        "bot_response": "Thank you for your response.",
        "sentiment": 0.5,
    }

    response = crud.create_response(db=test_db, response_data=response_data)

    assert response is not None
    assert response.id is not None
    assert response.interview_id == test_interview.id
    assert response.question_id == 1
    assert response.employee_message == response_data["employee_message"]
    assert response.bot_response == response_data["bot_response"]
    assert response.sentiment == 0.5
    assert response.created_at is not None


def test_get_responses_by_interview(test_db: Session, test_interview, test_response):
    """Test retrieving all responses for a specific interview."""
    # Ensure the test_response fixture is linked to the test_interview
    test_response.interview_id = test_interview.id
    test_db.commit()

    # Create another response for the same interview
    response_data_2 = {
        "interview_id": test_interview.id,
        "question_id": 2,
        "employee_message": "Second answer.",
        "bot_response": "Got it.",
    }
    crud.create_response(db=test_db, response_data=response_data_2)

    responses = crud.get_responses_by_interview(
        db=test_db, interview_id=test_interview.id
    )

    assert responses is not None
    assert len(responses) >= 2  # At least the fixture and the one we created
    assert all(r.interview_id == test_interview.id for r in responses)
    assert any(r.id == test_response.id for r in responses)
    assert any(r.question_id == 2 for r in responses)


def test_get_responses_by_interview_none(test_db: Session):
    """Test retrieving responses for a non-existent interview returns empty list."""
    responses = crud.get_responses_by_interview(db=test_db, interview_id=99999)
    assert responses is not None
    assert len(responses) == 0


def test_get_latest_response_by_question(test_db: Session, test_interview):
    """Test retrieving the latest response for a specific question in an interview."""
    interview_id = test_interview.id
    question_id = 5

    # Create multiple responses for the same question
    response_data_1 = {
        "interview_id": interview_id,
        "question_id": question_id,
        "employee_message": "First attempt.",
        "bot_response": "...",
    }
    crud.create_response(db=test_db, response_data=response_data_1)

    # Simulate a short delay
    import time

    time.sleep(0.01)

    response_data_2 = {
        "interview_id": interview_id,
        "question_id": question_id,
        "employee_message": "Second, better attempt.",
        "bot_response": "...",
    }
    r2 = crud.create_response(db=test_db, response_data=response_data_2)

    latest_response = crud.get_latest_response_by_question(
        db=test_db, interview_id=interview_id, question_id=question_id
    )

    assert latest_response is not None
    assert latest_response.id == r2.id
    assert latest_response.employee_message == response_data_2["employee_message"]


def test_get_latest_response_by_question_none(test_db: Session, test_interview):
    """Test retrieving latest response when no response exists for the question."""
    latest_response = crud.get_latest_response_by_question(
        db=test_db,
        interview_id=test_interview.id,
        question_id=999,  # Non-existent question ID for this test
    )
    assert latest_response is None
