from sqlalchemy.orm import Session
from typing import Optional
from . import models
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


# User operations
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def create_user(
    db: Session, username: str, email: str, password: str, role: str = "employee"
):
    hashed_password = get_password_hash(password)
    db_user = models.User(
        username=username, email=email, hashed_password=hashed_password, role=role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: int, **kwargs):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if not db_user:
        return None

    # Update password if provided
    if "password" in kwargs:
        kwargs["hashed_password"] = get_password_hash(kwargs.pop("password"))

    # Update other fields
    for key, value in kwargs.items():
        if hasattr(db_user, key):
            setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False


# Exit Interview operations
def create_exit_interview(db: Session, user_id: int, interviewer_id: int = None):
    db_interview = models.ExitInterview(user_id=user_id, interviewer_id=interviewer_id)
    db.add(db_interview)
    db.commit()
    db.refresh(db_interview)
    return db_interview


def get_exit_interview(db: Session, interview_id: int):
    return (
        db.query(models.ExitInterview)
        .filter(models.ExitInterview.id == interview_id)
        .first()
    )


def get_user_exit_interviews(db: Session, user_id: int):
    return (
        db.query(models.ExitInterview)
        .filter(models.ExitInterview.user_id == user_id)
        .all()
    )


def update_exit_interview(db: Session, interview_id: int, **kwargs):
    db_interview = (
        db.query(models.ExitInterview)
        .filter(models.ExitInterview.id == interview_id)
        .first()
    )
    if not db_interview:
        return None

    for key, value in kwargs.items():
        if hasattr(db_interview, key):
            setattr(db_interview, key, value)

    db.commit()
    db.refresh(db_interview)
    return db_interview


def delete_exit_interview(db: Session, interview_id: int):
    db_interview = (
        db.query(models.ExitInterview)
        .filter(models.ExitInterview.id == interview_id)
        .first()
    )
    if db_interview:
        db.delete(db_interview)
        db.commit()
        return True
    return False


# Question operations
def create_question(db: Session, text: str, category: str = None):
    db_question = models.Question(text=text, category=category)
    db.add(db_question)
    db.commit()
    db.refresh(db_question)
    return db_question


def get_question(db: Session, question_id: int):
    return db.query(models.Question).filter(models.Question.id == question_id).first()


def get_questions(
    db: Session, category: Optional[str] = None, skip: int = 0, limit: int = 100
):
    query = db.query(models.Question)
    if category:
        query = query.filter(models.Question.category == category)
    return query.offset(skip).limit(limit).all()


def update_question(db: Session, question_id: int, **kwargs):
    db_question = (
        db.query(models.Question).filter(models.Question.id == question_id).first()
    )
    if not db_question:
        return None

    for key, value in kwargs.items():
        if hasattr(db_question, key):
            setattr(db_question, key, value)

    db.commit()
    db.refresh(db_question)
    return db_question


def delete_question(db: Session, question_id: int):
    db_question = (
        db.query(models.Question).filter(models.Question.id == question_id).first()
    )
    if db_question:
        db.delete(db_question)
        db.commit()
        return True
    return False


# Interview Response operations
def create_interview_response(
    db: Session, interview_id: int, question_id: int, response_text: str
):
    db_response = models.InterviewResponse(
        interview_id=interview_id, question_id=question_id, response_text=response_text
    )
    db.add(db_response)
    db.commit()
    db.refresh(db_response)
    return db_response


def get_interview_responses(db: Session, interview_id: int):
    return (
        db.query(models.InterviewResponse)
        .filter(models.InterviewResponse.interview_id == interview_id)
        .all()
    )


def update_interview_response(db: Session, response_id: int, response_text: str):
    db_response = (
        db.query(models.InterviewResponse)
        .filter(models.InterviewResponse.id == response_id)
        .first()
    )

    if not db_response:
        return None

    db_response.response_text = response_text
    db.commit()
    db.refresh(db_response)
    return db_response


def delete_interview_response(db: Session, response_id: int):
    db_response = (
        db.query(models.InterviewResponse)
        .filter(models.InterviewResponse.id == response_id)
        .first()
    )

    if db_response:
        db.delete(db_response)
        db.commit()
        return True
    return False
