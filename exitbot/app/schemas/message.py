"""
Pydantic models for handling messages within an interview.
"""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict


class MessageRole(str, Enum):
    """Enumeration for the role of the message sender."""

    USER = "user"
    ASSISTANT = "assistant"


class MessageBase(BaseModel):
    """Base schema for message content."""

    content: str = Field(..., description="The textual content of the message")


class MessageCreate(MessageBase):
    """Schema for creating a new message (typically from the user)."""

    # Role might be implicitly 'user' when creating, or set by the endpoint
    pass


class Message(MessageBase):
    """Schema representing a message record, used for API responses."""

    id: int = Field(
        ...,
        description="Unique identifier for the message (note: often faked in list responses)",
    )
    interview_id: int = Field(
        ..., description="ID of the interview this message belongs to"
    )
    role: MessageRole = Field(
        ..., description="The role of the sender (user or assistant)"
    )
    created_at: datetime = Field(
        ..., description="Timestamp when the message was created"
    )

    model_config = ConfigDict(from_attributes=True)
