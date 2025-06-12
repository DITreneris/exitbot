from datetime import datetime, date
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, ConfigDict


class ReportBase(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    department: Optional[str] = None


class ReportCreate(BaseModel):
    """Schema for creating a new report"""

    interview_id: int
    summary: str
    themes: List[Dict[str, Any]]
    sentiment_score: Optional[float] = None
    recommendations: Optional[List[str]] = None


class Report(ReportCreate):
    """Schema for a report with additional fields"""

    id: int
    generated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SummaryStats(BaseModel):
    total_interviews: int
    completed_interviews: int
    in_progress_interviews: int
    average_sentiment: Optional[float] = None
    top_exit_reasons: List[Dict[str, Any]]


class DepartmentBreakdown(BaseModel):
    department: str
    interview_count: int
    sentiment_score: Optional[float] = None


class DepartmentReport(BaseModel):
    departments: List[DepartmentBreakdown]
