"""
Unit tests for interview CRUD operations.
"""
from sqlalchemy.orm import Session
from datetime import datetime, date

from exitbot.app.db import crud
from exitbot.app.schemas.interview import InterviewStatus


def test_create_interview(test_db: Session, test_employee):
    """Test creating a new interview successfully."""
    employee_id = test_employee.id
    title = "Test Interview CRUD"
    exit_date = date(2025, 12, 31)
    status = InterviewStatus.SCHEDULED

    interview = crud.create_interview(
        db=test_db,
        employee_id=employee_id,
        title=title,
        exit_date=exit_date,
        status=status,
    )

    assert interview is not None
    assert interview.id is not None
    assert interview.employee_id == employee_id
    assert interview.title == title
    assert interview.exit_date == exit_date
    assert interview.status == status
    assert interview.created_at is not None


def test_get_interview(test_db: Session, test_interview):
    """Test retrieving an interview by ID."""
    fetched_interview = crud.get_interview(db=test_db, interview_id=test_interview.id)

    assert fetched_interview is not None
    assert fetched_interview.id == test_interview.id
    assert fetched_interview.employee_id == test_interview.employee_id
    assert fetched_interview.title == test_interview.title


def test_get_interview_not_found(test_db: Session):
    """Test retrieving a non-existent interview returns None."""
    fetched_interview = crud.get_interview(db=test_db, interview_id=99999)
    assert fetched_interview is None


def test_get_interviews_by_employee(test_db: Session, test_employee, test_interview):
    """Test retrieving interviews for a specific employee."""
    # Ensure the test_interview fixture belongs to test_employee
    test_interview.employee_id = test_employee.id
    test_db.commit()

    interviews = crud.get_interviews_by_employee(
        db=test_db, employee_id=test_employee.id
    )

    assert interviews is not None
    assert len(interviews) >= 1
    assert any(i.id == test_interview.id for i in interviews)
    assert all(i.employee_id == test_employee.id for i in interviews)


def test_update_interview_status(test_db: Session, test_interview):
    """Test updating the status of an interview."""
    interview_id = test_interview.id
    new_status = InterviewStatus.IN_PROGRESS

    updated_interview = crud.update_interview_status(
        db=test_db, interview_id=interview_id, status=new_status.value
    )

    assert updated_interview is not None
    assert updated_interview.id == interview_id
    assert updated_interview.status == new_status.value
    assert updated_interview.updated_at is not None

    # Verify completion timestamp is set for COMPLETED status
    completed_status = InterviewStatus.COMPLETED
    completed_interview = crud.update_interview_status(
        db=test_db, interview_id=interview_id, status=completed_status.value
    )
    assert completed_interview.completed_at is not None


def test_update_interview_by_id(test_db: Session, test_interview):
    """Test updating interview fields by ID using a dictionary."""
    interview_id = test_interview.id
    update_data = {
        "title": "Updated CRUD Title",
        "description": "Updated description",
        "end_date": datetime.utcnow(),
    }

    updated_interview = crud.update_interview_by_id(
        db=test_db, interview_id=interview_id, update_dict=update_data
    )

    assert updated_interview is not None
    assert updated_interview.id == interview_id
    assert updated_interview.title == update_data["title"]
    assert updated_interview.description == update_data["description"]
    assert updated_interview.end_date is not None  # Check if date was set
    assert updated_interview.updated_at is not None


def test_update_interview_by_id_not_found(test_db: Session):
    """Test updating a non-existent interview by ID returns None."""
    update_data = {"title": "Won't Update"}
    updated_interview = crud.update_interview_by_id(
        db=test_db, interview_id=99999, update_dict=update_data
    )
    assert updated_interview is None


# Add tests for get_all_interviews if needed
# Add tests for update_interview if it's used differently than update_interview_by_id
