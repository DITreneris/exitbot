from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from exitbot.app.db.models import Response


# Response operations
def create_response(db: Session, response_data: Dict[str, Any]) -> Response:
    db_response = Response(**response_data)
    db.add(db_response)
    db.commit()
    db.refresh(db_response)
    return db_response


def get_responses_by_interview(db: Session, interview_id: int) -> List[Response]:
    return db.query(Response).filter(Response.interview_id == interview_id).all()


def get_latest_response_by_question(
    db: Session, interview_id: int, question_id: int
) -> Optional[Response]:
    return (
        db.query(Response)
        .filter(
            Response.interview_id == interview_id, Response.question_id == question_id
        )
        .order_by(Response.created_at.desc())
        .first()
    )
