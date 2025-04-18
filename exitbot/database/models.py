from datetime import datetime
import enum
from typing import Optional, List

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Enum, Text
from sqlalchemy.orm import relationship

from exitbot.database.database import Base

class UserRole(enum.Enum):
    ADMIN = "admin"
    HR = "hr"
    EMPLOYEE = "employee"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    hashed_password = Column(String)
    role = Column(Enum(UserRole), default=UserRole.EMPLOYEE)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    exit_interviews = relationship("ExitInterview", back_populates="employee")
    
class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False)
    category = Column(String, nullable=False)
    question_type = Column(String, nullable=False)  # rating, yes_no, text, multiple_choice
    options = Column(String, nullable=True)  # JSON string for multiple choice options
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    answers = relationship("Answer", back_populates="question")

class ExitInterview(Base):
    __tablename__ = "exit_interviews"
    
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="pending")  # pending, in_progress, completed
    completion_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employee = relationship("User", back_populates="exit_interviews")
    answers = relationship("Answer", back_populates="exit_interview")

class Answer(Base):
    __tablename__ = "answers"
    
    id = Column(Integer, primary_key=True, index=True)
    exit_interview_id = Column(Integer, ForeignKey("exit_interviews.id"))
    question_id = Column(Integer, ForeignKey("questions.id"))
    answer_text = Column(Text, nullable=True)
    answer_rating = Column(Integer, nullable=True)
    answer_boolean = Column(Boolean, nullable=True)
    answer_choice = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    exit_interview = relationship("ExitInterview", back_populates="answers")
    question = relationship("Question", back_populates="answers") 