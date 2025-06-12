from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# Base schema for Response
class ResponseBase(BaseModel):
    question: str = Field(..., description="The question asked during the interview.")
    answer: Optional[str] = Field(
        None, description="The answer provided by the employee."
    )
    feedback: Optional[str] = Field(
        None, description="Feedback or notes related to the response."
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Any additional metadata."
    )


# Schema for creating a Response (input)
class ResponseCreate(ResponseBase):
    interview_id: int = Field(
        ..., description="The ID of the interview this response belongs to."
    )
    pass


# Schema for updating a Response (input, all fields optional)
class ResponseUpdate(BaseModel):
    question: Optional[str] = Field(None, description="The question asked.")
    answer: Optional[str] = Field(None, description="The answer provided.")
    feedback: Optional[str] = Field(None, description="Feedback or notes.")
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Any additional metadata."
    )


# Schema for representing a Response in the database (includes DB fields)
class ResponseInDBBase(ResponseBase):
    id: int
    interview_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Schema for returning a Response to the client (output)
class Response(ResponseInDBBase):
    pass
