"""
Pydantic models for dashboard and admin API responses.
"""
from typing import Dict, List, Optional, Any
from datetime import datetime

from pydantic import BaseModel, Field


class ActivityData(BaseModel):
    """Activity timeline data point."""

    date: str = Field(..., description="Date in ISO format (YYYY-MM-DD)")
    count: int = Field(..., description="Number of interviews on this date")


class DashboardStatistics(BaseModel):
    """Dashboard overview statistics."""

    total_users: int = Field(..., description="Total number of users in the system")
    total_interviews: int = Field(..., description="Total number of interviews")
    recent_interviews: int = Field(
        ..., description="Number of interviews in the selected time range"
    )
    interviews_by_status: Dict[str, int] = Field(
        ..., description="Counts of interviews by status"
    )
    completion_rate: float = Field(
        ..., description="Percentage of completed interviews"
    )
    average_sentiment: Optional[float] = Field(
        None,
        description="Average sentiment score across recent interviews (if available)",
    )
    time_range: str = Field(
        ...,
        description="Time range for the statistics (week, month, quarter, year, all)",
    )


class UserActivityStats(BaseModel):
    """User activity statistics."""

    user_id: int = Field(..., description="User ID")
    full_name: str = Field(..., description="User's full name")
    email: str = Field(..., description="User's email")
    total_interviews: int = Field(
        ..., description="Total number of interviews for this user"
    )
    completed_interviews: int = Field(..., description="Number of completed interviews")
    in_progress_interviews: int = Field(
        ..., description="Number of in-progress interviews"
    )
    completion_rate: float = Field(
        ..., description="Percentage of completed interviews"
    )
    avg_completion_time_minutes: Optional[float] = Field(
        None, description="Average time to complete an interview in minutes"
    )
    total_messages: int = Field(
        ..., description="Total number of messages in all interviews"
    )


class ThemeCount(BaseModel):
    """Theme frequency data."""

    theme: str = Field(..., description="Theme name or category")
    count: int = Field(..., description="Number of occurrences")


class InsightsData(BaseModel):
    """Interview insights and trends data."""

    total_analyzed: int = Field(..., description="Total number of interviews analyzed")
    time_range: str = Field(
        ..., description="Time range for the insights (month, quarter, year, all)"
    )
    common_themes: List[Dict[str, Any]] = Field(
        ..., description="Most common themes mentioned in interviews"
    )
    avg_satisfaction: Optional[float] = Field(
        None, description="Average satisfaction score (if available)"
    )


class ExportData(BaseModel):
    """Data export container."""

    generated_at: datetime = Field(
        ..., description="Timestamp when the export was generated"
    )
    start_date: datetime = Field(..., description="Start date for the exported data")
    end_date: datetime = Field(..., description="End date for the exported data")
    format: str = Field(..., description="Export format (json, csv)")
    total_records: int = Field(..., description="Total number of records in the export")
    data: List[Dict[str, Any]] = Field(..., description="The exported data")


class PasswordReset(BaseModel):
    """Password reset request data."""

    new_password: str = Field(..., description="New password", min_length=8)


class Message(BaseModel):
    """Simple message response."""

    message: str = Field(..., description="Response message")


class BulkInterviewStatusUpdate(BaseModel):
    """Bulk interview status update request."""

    interview_ids: List[int] = Field(..., description="List of interview IDs to update")
    new_status: str = Field(
        ...,
        description="New status for the interviews",
        pattern="^(scheduled|in_progress|completed|cancelled)$",
    )


class BulkUpdateResponse(BaseModel):
    """Bulk update operation response."""

    success_count: int = Field(..., description="Number of successfully updated items")
    failure_count: int = Field(..., description="Number of failed updates")
    failures: List[Dict[str, Any]] = Field(..., description="Details of failed updates")
