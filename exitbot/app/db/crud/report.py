from typing import Optional
from sqlalchemy.orm import Session

from exitbot.app.db.models import Report, Interview
from exitbot.app.schemas.report import ReportCreate # Assuming ReportCreate schema exists

# Report CRUD operations

def get_by_interview_id(db: Session, *, interview_id: int) -> Optional[Report]:
    """Get a report by the associated interview ID."""
    return db.query(Report).filter(Report.interview_id == interview_id).first()

def create_report(db: Session, *, report_in: ReportCreate, creator_id: int) -> Report:
    """Create a new report."""
    # Here you might transform report_in (dict or schema) to model fields
    # Assuming ReportCreate directly maps or needs adaptation
    db_report = Report(
        **report_in.model_dump(), # Use model_dump() for Pydantic v2
        creator_id=creator_id,
        interview_id=report_in.interview_id # Ensure interview_id is part of ReportCreate
    )
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return db_report

# Add other CRUD functions as needed (get, update, delete) 