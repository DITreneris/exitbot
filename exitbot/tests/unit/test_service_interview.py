"""
Unit tests for InterviewService.
"""
import pytest
from unittest.mock import patch
from datetime import datetime, date

from sqlalchemy.orm import Session

from exitbot.app.services.interview import InterviewService
from exitbot.app.db.models import Interview
from exitbot.app.schemas.interview import InterviewStatus


@pytest.fixture
def mock_crud():
    """Fixture to mock CRUD operations"""
    with patch("exitbot.app.services.interview.crud", autospec=True) as mock:
        yield mock


def test_start_interview(test_db: Session, mock_crud, test_employee):
    """Test starting a new interview."""
    employee_id = test_employee.id
    exit_date = date(2025, 12, 31)

    # Mock the create_interview CRUD call
    mock_interview = Interview(
        id=1,
        employee_id=employee_id,
        exit_date=exit_date,
        status=InterviewStatus.SCHEDULED,
        created_at=datetime.utcnow(),
    )
    mock_crud.create_interview.return_value = mock_interview

    # Mock the _ensure_default_questions call (or its underlying CRUD calls)
    # For simplicity, let's just mock the service method directly here
    with patch.object(
        InterviewService, "_ensure_default_questions", return_value=None
    ) as mock_ensure:
        interview = InterviewService.start_interview(
            db=test_db, employee_id=employee_id, exit_date=exit_date
        )

        # Assert CRUD was called correctly
        mock_crud.create_interview.assert_called_once_with(
            test_db,
            employee_id,
            exit_date,
            title=None,  # Check default title if applicable
            status=InterviewStatus.SCHEDULED,
        )

        # Assert _ensure_default_questions was called
        mock_ensure.assert_called_once_with(test_db)

        # Assert the correct interview object is returned
        assert interview == mock_interview
        assert interview.id == 1
        assert interview.employee_id == employee_id
        assert interview.exit_date == exit_date


def test_complete_interview(test_db: Session, mock_crud, test_interview):
    """Test marking an interview as complete."""
    interview_id = test_interview.id

    # Mock the get_interview and update_interview_by_id CRUD calls
    # Simulate the interview object that get_interview would return
    mock_interview_existing = Interview(**test_interview.__dict__)
    mock_crud.get_interview.return_value = mock_interview_existing

    # Mock the update_interview_by_id call to return the updated object
    mock_updated_interview = Interview(**test_interview.__dict__)
    mock_updated_interview.status = InterviewStatus.COMPLETED.value
    mock_updated_interview.completed_at = datetime.utcnow()
    mock_crud.update_interview_by_id.return_value = mock_updated_interview

    completed_interview = InterviewService.complete_interview(
        db=test_db, interview_id=interview_id
    )

    # Assert get_interview was called
    mock_crud.get_interview.assert_called_once_with(test_db, interview_id)

    # Assert update_interview_by_id was called with correct status and timestamp
    mock_crud.update_interview_by_id.assert_called_once()
    call_args = mock_crud.update_interview_by_id.call_args[0]  # Get positional args
    assert call_args[0] == test_db
    assert call_args[1] == interview_id
    update_dict = call_args[2]
    assert update_dict["status"] == InterviewStatus.COMPLETED.value
    assert "completed_at" in update_dict
    assert isinstance(update_dict["completed_at"], datetime)

    # Assert the correct, updated interview object is returned
    assert completed_interview == mock_updated_interview
    assert completed_interview.status == InterviewStatus.COMPLETED.value
    assert completed_interview.completed_at is not None


def test_complete_interview_not_found(test_db: Session, mock_crud):
    """Test completing a non-existent interview raises ValueError."""
    interview_id = 99999
    mock_crud.get_interview.return_value = None  # Simulate interview not found

    with pytest.raises(ValueError, match=f"Interview with ID {interview_id} not found"):
        InterviewService.complete_interview(db=test_db, interview_id=interview_id)

    # Verify update was not called
    mock_crud.update_interview_by_id.assert_not_called()


# Note: Tests for process_message would be more complex, requiring mocking
# of LLM calls and potentially get_current_question logic.
# Tests for private methods like _ensure_default_questions, _get_question_history,
# and _determine_next_question are generally not recommended,
# test their effects through the public methods that use them.
