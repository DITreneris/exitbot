from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import logging

from exitbot.app.db.models import Interview
from exitbot.app.schemas.interview import InterviewStatus

# Interview operations
def create_interview(db: Session, employee_id: int, title: Optional[str] = None, exit_date: Optional[datetime] = None, status: InterviewStatus = InterviewStatus.SCHEDULED, created_by_id: Optional[int] = None) -> Interview:
    db_interview = Interview(
        employee_id=employee_id,
        title=title,
        exit_date=exit_date,
        status=status,
        created_by_id=created_by_id
    )
    db.add(db_interview)
    db.commit()
    db.refresh(db_interview)
    return db_interview

def get_interview(db: Session, interview_id: int) -> Optional[Interview]:
    return db.query(Interview).filter(Interview.id == interview_id).first()

def get_interviews_by_employee(db: Session, employee_id: int) -> List[Interview]:
    return db.query(Interview).filter(Interview.employee_id == employee_id).all()

def get_all_interviews(db: Session, skip: int = 0, limit: int = 100) -> List[Interview]:
    return db.query(Interview).offset(skip).limit(limit).all()

def update_interview_status(db: Session, interview_id: int, status: str) -> Optional[Interview]:
    db_interview = db.query(Interview).filter(Interview.id == interview_id).first()
    if db_interview:
        db_interview.status = status
        db_interview.updated_at = datetime.utcnow()
        if status == InterviewStatus.COMPLETED.value:
            db_interview.completed_at = datetime.utcnow()
        db.commit()
        db.refresh(db_interview)
    return db_interview

# Add a general update function
def update_interview(db: Session, db_interview: Interview, interview_in: Dict[str, Any]) -> Interview:
    """Update an interview with new data."""
    update_data = interview_in
    for field, value in update_data.items():
        # Only set attributes that are part of the model and are provided in the update
        if hasattr(db_interview, field) and value is not None:
            setattr(db_interview, field, value)
    
    # Ensure updated_at is set
    db_interview.updated_at = datetime.utcnow()
    
    db.add(db_interview) # Add the updated object to the session
    db.commit()
    db.refresh(db_interview)
    return db_interview 