from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from exitbot.app.db.models import Question


# Question operations
def create_question(db: Session, question_data: Dict[str, Any]) -> Question:
    db_question = Question(**question_data)
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question


def get_question(db: Session, question_id: int) -> Optional[Question]:
    return db.query(Question).filter(Question.id == question_id).first()


def get_all_questions(db: Session, skip: int = 0, limit: int = 100) -> List[Question]:
    return (
        db.query(Question)
        .filter(Question.is_active)
        .order_by(Question.order_num)
        .offset(skip)
        .limit(limit)
        .all()
    )
