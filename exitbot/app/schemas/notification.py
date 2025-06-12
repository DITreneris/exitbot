"""
Pydantic models for notifications.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class NotificationType(str, Enum):
    """Types of notifications."""

    SYSTEM = "system"
    INTERVIEW = "interview"
    USER = "user"
    REPORT = "report"
    ADMIN = "admin"


class NotificationPriority(str, Enum):
    """Priority levels for notifications."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class NotificationStatus(str, Enum):
    """Status of a notification."""

    UNREAD = "unread"
    READ = "read"
    ARCHIVED = "archived"


class NotificationCreate(BaseModel):
    """Schema for creating a new notification."""

    title: str = Field(
        ..., description="Notification title", min_length=1, max_length=255
    )
    content: str = Field(..., description="Notification content", min_length=1)
    notification_type: NotificationType = Field(
        default=NotificationType.SYSTEM, description="Type of notification"
    )
    priority: NotificationPriority = Field(
        default=NotificationPriority.MEDIUM,
        description="Priority level of the notification",
    )
    recipient_id: int = Field(..., description="User ID of the recipient")
    reference_id: Optional[int] = Field(
        None, description="Optional ID of the referenced entity (e.g., interview ID)"
    )
    reference_type: Optional[str] = Field(
        None, description="Optional type of the referenced entity (e.g., 'interview')"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None, description="Additional metadata about the notification"
    )

    @field_validator("reference_type")
    def validate_reference_type(cls, v, info):
        """Validate that reference_type is provided if reference_id is provided."""
        values = info.data
        if (
            "reference_id" in values
            and values.get("reference_id") is not None
            and v is None
        ):
            raise ValueError(
                "reference_type must be provided if reference_id is provided"
            )
        return v


class NotificationUpdate(BaseModel):
    """Schema for updating a notification."""

    status: Optional[NotificationStatus] = Field(
        None, description="Status of the notification"
    )
    read_at: Optional[datetime] = Field(
        None, description="When the notification was read"
    )

    @field_validator("read_at")
    def validate_read_at(cls, v, info):
        """Set read_at automatically when status is changed to READ."""
        values = info.data
        if (
            "status" in values
            and values.get("status") == NotificationStatus.READ
            and v is None
        ):
            return datetime.utcnow()
        return v


class Notification(BaseModel):
    """Schema for a notification."""

    id: int = Field(..., description="Unique notification ID")
    title: str = Field(..., description="Notification title")
    content: str = Field(..., description="Notification content")
    notification_type: NotificationType = Field(..., description="Type of notification")
    priority: NotificationPriority = Field(
        ..., description="Priority level of the notification"
    )
    status: NotificationStatus = Field(..., description="Status of the notification")
    recipient_id: int = Field(..., description="User ID of the recipient")
    reference_id: Optional[int] = Field(
        None, description="Optional ID of the referenced entity"
    )
    reference_type: Optional[str] = Field(
        None, description="Optional type of the referenced entity"
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    created_at: datetime = Field(..., description="When the notification was created")
    updated_at: Optional[datetime] = Field(
        None, description="When the notification was last updated"
    )
    read_at: Optional[datetime] = Field(
        None, description="When the notification was read"
    )

    model_config = {"from_attributes": True}


class NotificationList(BaseModel):
    """Schema for a list of notifications."""

    total: int = Field(..., description="Total number of notifications")
    unread_count: int = Field(..., description="Number of unread notifications")
    items: List[Notification] = Field(..., description="List of notifications")


class NotificationBulkUpdate(BaseModel):
    """Schema for bulk updating notifications."""

    notification_ids: List[int] = Field(
        ..., description="List of notification IDs to update"
    )
    status: NotificationStatus = Field(
        ..., description="New status for the notifications"
    )


class NotificationBulkUpdateResponse(BaseModel):
    """Schema for response to bulk update operation."""

    success_count: int = Field(
        ..., description="Number of notifications successfully updated"
    )
    failure_count: int = Field(..., description="Number of failed updates")
    failures: List[Dict[str, Any]] = Field(..., description="Details of failed updates")


class NotificationPreferences(BaseModel):
    """Schema for user notification preferences."""

    email_notifications: bool = Field(
        default=True, description="Whether to send email notifications"
    )
    in_app_notifications: bool = Field(
        default=True, description="Whether to send in-app notifications"
    )
    notification_types: Dict[str, bool] = Field(
        default_factory=lambda: {
            NotificationType.SYSTEM.value: True,
            NotificationType.INTERVIEW.value: True,
            NotificationType.USER.value: True,
            NotificationType.REPORT.value: True,
            NotificationType.ADMIN.value: True,
        },
        description="Preferences for different notification types",
    )

    model_config = {"from_attributes": True}
