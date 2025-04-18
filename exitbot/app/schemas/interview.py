from datetime import datetime, date
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, field_validator, model_validator
from .response import Response

# Question schemas
class QuestionBase(BaseModel):
    text: str
    order_num: Optional[int] = None
    category: Optional[str] = None

class QuestionCreate(QuestionBase):
    pass

class Question(QuestionBase):
    id: int
    is_active: bool
    
    model_config = {"from_attributes": True}

# Response schemas
class ResponseBase(BaseModel):
    interview_id: int
    question_id: Optional[int]
    employee_message: str
    bot_response: Optional[str] = None
    sentiment: Optional[float] = None

class ResponseCreate(ResponseBase):
    pass

class Response(ResponseBase):
    id: int
    created_at: datetime
    
    model_config = {"from_attributes": True}

# Interview schemas
class InterviewStatus(str, Enum):
    """Valid interview status values."""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class InterviewType(str, Enum):
    """Types of interviews available in the system."""
    EXIT = "exit"
    ONBOARDING = "onboarding"
    PERFORMANCE = "performance"
    SATISFACTION = "satisfaction"
    CUSTOM = "custom"

class InterviewBase(BaseModel):
    """Base schema for interview data."""
    title: str = Field(..., description="Interview title", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Interview description")
    interview_type: InterviewType = Field(
        default=InterviewType.EXIT,
        description="Type of interview"
    )
    template_id: Optional[int] = Field(
        None, 
        description="ID of the template used for this interview"
    )
    scheduled_at: Optional[datetime] = Field(
        None, 
        description="Time when the interview is scheduled"
    )
    interview_metadata: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Additional metadata about the interview"
    )

class InterviewCreate(BaseModel):
    """Schema for creating a new interview."""
    employee_id: int = Field(..., description="User ID of the employee being interviewed")
    title: str = Field(..., description="Interview title")
    status: InterviewStatus = Field(
        default=InterviewStatus.SCHEDULED,
        description="Current status of the interview"
    )
    exit_date: Optional[date] = Field(None, description="Exit date of the interview")
    
    @field_validator('status')
    def check_status_valid(cls, value):
        if value not in InterviewStatus.__members__.values():
            raise ValueError(f"Invalid status: {value}")
        return value

class InterviewUpdateBase(BaseModel):
    title: Optional[str] = Field(None, description="Interview title")
    description: Optional[str] = Field(None, description="Description of the interview")
    status: Optional[InterviewStatus] = Field(None, description="Current status of the interview")
    start_date: Optional[datetime] = Field(None, description="Time when the interview started")
    scheduled_at: Optional[datetime] = Field(None, description="Scheduled time for the interview")
    end_date: Optional[datetime] = Field(None, description="Time when the interview ended")
    completed_at: Optional[datetime] = Field(None, description="Time when the interview was completed")
    interview_metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata about the interview")
    exit_date: Optional[date] = Field(None, description="Exit date of the interview")

    @model_validator(mode='after')
    def check_dates(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError("End date cannot be earlier than start date")
        if self.completed_at and self.start_date and self.completed_at < self.start_date:
            raise ValueError("Completion date cannot be earlier than start date")
        return self

class InterviewUpdate(InterviewUpdateBase):
    """Schema for updating an interview."""
    pass

class InterviewInDBBase(InterviewUpdateBase):
    """Base schema for interview data stored in the database."""
    id: int = Field(..., description="Unique identifier for the interview")
    employee_id: int = Field(..., description="User ID of the employee being interviewed")
    created_by_id: Optional[int] = Field(None, description="User ID of the creator")
    created_at: datetime = Field(..., description="Time the interview was created")
    updated_at: Optional[datetime] = Field(None, description="Time the interview was last updated")
    completed_at: Optional[datetime] = Field(None, description="Time the interview was completed")
    start_date: Optional[datetime] = Field(None, description="Start date of the interview")
    end_date: Optional[datetime] = Field(None, description="End date of the interview")
    exit_date: Optional[date] = Field(None, description="Exit date of the interview")
    
    model_config = {"from_attributes": True}

class Interview(InterviewInDBBase):
    """Schema for returning interview data to the client."""
    responses: List[Response] = Field([], description="List of responses associated with the interview")

class InterviewInDB(InterviewInDBBase):
    """Schema representing the full interview data as stored in the database."""
    pass

class InterviewProgress(BaseModel):
    """Schema for tracking the progress of an interview."""
    current_question_index: int
    total_questions: int
    is_complete: bool = False

class InterviewComplete(BaseModel):
    interview_id: int

class InterviewList(BaseModel):
    """Schema for a list of interviews."""
    total: int = Field(..., description="Total number of interviews")
    items: List[Interview] = Field(..., description="List of interviews")

class InterviewDetail(Interview):
    responses: List[Response] = []

# Message schema for interaction
class MessageRole(str, Enum):
    """Message role types."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class MessageCreate(BaseModel):
    """Schema for creating a new message."""
    content: str = Field(..., description="Message content", min_length=1)
    role: MessageRole = Field(
        default=MessageRole.USER,
        description="Role of the message sender (user, assistant, system)"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Optional metadata for the message"
    )

class Message(MessageCreate):
    """Schema for a message with additional fields."""
    id: int = Field(..., description="Unique message ID")
    interview_id: int = Field(..., description="ID of the interview this message belongs to")
    created_at: datetime = Field(..., description="Time the message was created")
    updated_at: Optional[datetime] = Field(None, description="Time the message was last updated")
    
    model_config = {"from_attributes": True}

class MessageList(BaseModel):
    """Schema for a list of messages."""
    total: int = Field(..., description="Total number of messages")
    items: List[Message] = Field(..., description="List of messages")

class InterviewResponse(BaseModel):
    response: str
    current_question: Optional[Question] = None
    is_complete: bool = False

class ReportTheme(BaseModel):
    """Schema for a theme in an interview report."""
    name: str = Field(..., description="Theme name")
    count: int = Field(..., description="Number of occurrences")
    sentiment: Optional[float] = Field(
        None, 
        description="Sentiment score for this theme (-1.0 to 1.0)"
    )
    examples: List[str] = Field(
        default_factory=list,
        description="Example quotes related to this theme"
    )

class Report(BaseModel):
    """Schema for an interview report."""
    id: int = Field(..., description="Unique report ID")
    interview_id: int = Field(..., description="ID of the interview this report is for")
    summary: str = Field(..., description="Executive summary of the interview")
    themes: List[Dict[str, Any]] = Field(
        ..., 
        description="Key themes identified in the interview"
    )
    sentiment_score: Optional[float] = Field(
        None, 
        description="Overall sentiment score for the interview (-1.0 to 1.0)"
    )
    recommendations: Optional[List[str]] = Field(
        None, 
        description="Recommendations based on the interview"
    )
    generated_at: datetime = Field(..., description="Time the report was generated")
    metadata: Optional[Dict[str, Any]] = Field(
        default=None, 
        description="Additional metadata about the report"
    )

    model_config = {"from_attributes": True}

class InterviewTemplate(BaseModel):
    """Schema for interview templates."""
    id: int = Field(..., description="Unique template ID")
    name: str = Field(..., description="Template name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Template description")
    interview_type: InterviewType = Field(..., description="Type of interview this template is for")
    system_prompt: str = Field(..., description="System prompt for LLM", min_length=10)
    initial_message: str = Field(..., description="Initial message to display to the user", min_length=1)
    questions: List[str] = Field(..., description="List of questions for the interview")
    created_by_id: int = Field(..., description="User ID of the admin who created the template")
    created_at: datetime = Field(..., description="Time the template was created")
    updated_at: Optional[datetime] = Field(None, description="Time the template was last updated")
    is_active: bool = Field(default=True, description="Whether the template is active")

    model_config = {"from_attributes": True}

class TemplateCreate(BaseModel):
    """Schema for creating a new template."""
    name: str = Field(..., description="Template name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Template description")
    interview_type: InterviewType = Field(..., description="Type of interview this template is for")
    system_prompt: str = Field(..., description="System prompt for LLM", min_length=10)
    initial_message: str = Field(..., description="Initial message to display to the user", min_length=1)
    questions: List[str] = Field(..., description="List of questions for the interview")

class TemplateUpdate(BaseModel):
    """Schema for updating a template."""
    name: Optional[str] = Field(None, description="Template name", min_length=1, max_length=255)
    description: Optional[str] = Field(None, description="Template description")
    system_prompt: Optional[str] = Field(None, description="System prompt for LLM", min_length=10)
    initial_message: Optional[str] = Field(None, description="Initial message to display to the user", min_length=1)
    questions: Optional[List[str]] = Field(None, description="List of questions for the interview")
    is_active: Optional[bool] = Field(None, description="Whether the template is active")

class TemplateList(BaseModel):
    """Schema for a list of templates."""
    total: int = Field(..., description="Total number of templates")
    items: List[InterviewTemplate] = Field(..., description="List of templates")

class Message(BaseModel):
    """Schema for a message in an interview"""
    interview_id: int
    message: str
    question_id: Optional[int] = None

class InterviewResponse(BaseModel):
    """Schema for an interview response"""
    response: str
    current_question: Optional[dict] = None
    is_complete: bool = False

class InterviewComplete(BaseModel):
    interview_id: int 