from datetime import datetime, date
from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, Text, Float, DateTime, Date, Enum as SqlEnum, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List

from exitbot.app.db.base import Base
from ..schemas.interview import InterviewStatus  # Use correct schema path

# Define Report class BEFORE User class due to relationship dependency
class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id"))
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id")) # Link to the User who created it
    summary: Mapped[str] = mapped_column(Text)
    sentiment_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    key_topics: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # Store as JSON string or similar
    recommendations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    report_url: Mapped[Optional[str]] = mapped_column(String, nullable=True) # Optional URL to a generated file

    # Relationships
    interview: Mapped["Interview"] = relationship() # Define relationship appropriately
    creator: Mapped["User"] = relationship(back_populates="created_reports")


class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=True)
    full_name: Mapped[str] = mapped_column(String)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    department: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Relationships
    interviews: Mapped[List["Interview"]] = relationship(
        back_populates="employee", 
        foreign_keys="Interview.employee_id"
    )
    created_reports: Mapped[List["Report"]] = relationship(back_populates="creator")
    
class Interview(Base):
    __tablename__ = "interviews"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_by_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[InterviewStatus] = mapped_column(SqlEnum(InterviewStatus), default=InterviewStatus.SCHEDULED)
    start_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    exit_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    interview_metadata: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    
    # Relationships
    employee: Mapped["User"] = relationship(
        back_populates="interviews",
        foreign_keys=[employee_id]
    )
    responses: Mapped[List["Response"]] = relationship(back_populates="interview")
    creator: Mapped[Optional["User"]] = relationship(foreign_keys=[created_by_id])
    
class Question(Base):
    __tablename__ = "questions"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    order_num: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    category: Mapped[str] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships
    responses: Mapped[List["Response"]] = relationship(back_populates="question")
    
class Response(Base):
    __tablename__ = "responses"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    interview_id: Mapped[int] = mapped_column(ForeignKey("interviews.id"))
    question_id: Mapped[Optional[int]] = mapped_column(ForeignKey("questions.id"), nullable=True)
    employee_message: Mapped[str] = mapped_column(Text)
    bot_response: Mapped[str] = mapped_column(Text)
    sentiment: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    interview: Mapped["Interview"] = relationship(back_populates="responses")
    question: Mapped["Question"] = relationship(back_populates="responses") 