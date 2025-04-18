"""
Admin dashboard API endpoints for analytics and reporting.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from sqlalchemy import func, select, cast, Float
from sqlalchemy.orm import Session

from exitbot.app.db import models
from exitbot.app.db import crud
from exitbot.app.schemas import dashboard as dashboard_schemas
from exitbot.app.schemas import user as user_schemas
from exitbot.app.schemas import interview as interview_schemas
from exitbot.app.schemas import report as report_schemas
from exitbot.app.api import deps
from exitbot.app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get(
    "/statistics", 
    response_model=dashboard_schemas.DashboardStatistics,
    summary="Get dashboard statistics",
    description="""
    Retrieve high-level statistics for the admin dashboard.
    # Only accessible to admin users. (Dependency Temporarily Removed for Debugging)
    """,
    response_description="Dashboard statistics",
    responses={
        200: {"description": "Success"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Admin privileges required"}
    }
)
async def get_dashboard_statistics(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
    time_range: str = Query(
        "month", 
        description="Time range for statistics", 
        pattern="^(week|month|quarter|year|all)$"
    )
) -> dashboard_schemas.DashboardStatistics:
    """
    Get overall dashboard statistics.
    
    Parameters:
    - time_range: Time period for statistics (week, month, quarter, year, all)
    
    Returns:
    - DashboardStatistics object with counts and metrics
    """
    
    # --- REMOVED TEMPORARY DEBUG Block ---
    # logger.warning("DEBUG: Returning hardcoded statistics data (Admin check disabled)")
    # statistics = dashboard_schemas.DashboardStatistics(
    #     total_users=10, # Dummy data
    #     total_interviews=5, # Dummy data
    #     recent_interviews=2, # Dummy data
    #     interviews_by_status={
    #         "scheduled": 1,
    #         "in_progress": 1,
    #         "completed": 2,
    #         "cancelled": 1
    #     }, # Dummy data
    #     completion_rate=40.0, # Dummy data (2 completed / 5 total)
    #     average_sentiment=0.5, # Dummy data (or None)
    #     time_range=time_range
    # )
    # return statistics
    # --- END TEMPORARY DEBUG ---

    # --- Begin Restoring Original Code ---
    # Calculate date range
    today = datetime.utcnow()
    if time_range == "week":
        start_date = today - timedelta(days=7)
    elif time_range == "month":
        start_date = today - timedelta(days=30)
    elif time_range == "quarter":
        start_date = today - timedelta(days=90)
    elif time_range == "year":
        start_date = today - timedelta(days=365)
    else:  # all
        start_date = datetime.min
    
    # Get counts from database
    total_users = db.query(func.count(models.User.id)).scalar()
    total_interviews = db.query(func.count(models.Interview.id)).scalar()
    
    # Count interviews by status
    interviews_by_status = {}
    for status_val in ["scheduled", "in_progress", "completed", "cancelled"]:
        count = db.query(func.count(models.Interview.id)).filter(
            models.Interview.status == status_val
        ).scalar()
        interviews_by_status[status_val] = count
    
    # Get recent interviews
    recent_interviews = db.query(models.Interview).filter(
        models.Interview.created_at >= start_date
    ).count()
    
    # Get completion rate
    if total_interviews > 0:
        completion_rate = interviews_by_status.get("completed", 0) / total_interviews * 100
    else:
        completion_rate = 0
    
    # Calculate average sentiment using database AVG function
    avg_sentiment = db.query(func.avg(models.Response.sentiment)).join(
        models.Interview, models.Response.interview_id == models.Interview.id
    ).filter(
        models.Interview.created_at >= start_date # Apply the date range filter
    ).scalar()

    # Convert to float if not None
    if avg_sentiment is not None:
        avg_sentiment = float(avg_sentiment)
        
    # Construct response
    statistics = dashboard_schemas.DashboardStatistics(
        total_users=total_users,
        total_interviews=total_interviews,
        recent_interviews=recent_interviews,
        interviews_by_status=interviews_by_status,
        completion_rate=round(completion_rate, 2),
        # Use the calculated avg_sentiment, handling None during rounding
        average_sentiment=round(avg_sentiment, 2) if avg_sentiment is not None else None,
        time_range=time_range
    )
    
    logger.info(f"Dashboard statistics retrieved by admin {current_user.id}")
    return statistics
    # --- End Original Code ---

    # --- REMOVED Temporary return block ---
    # temp_statistics = dashboard_schemas.DashboardStatistics(
    #     total_users=total_users, # Calculated
    #     total_interviews=total_interviews, # Calculated
    #     recent_interviews=recent_interviews, # Calculated
    #     interviews_by_status=interviews_by_status, # Calculated
    #     completion_rate=0.0, # Placeholder
    #     average_sentiment=None, # Placeholder
    #     time_range=time_range
    # )
    # logger.info(f"Dashboard statistics retrieved by admin {current_user.id} (Partial Data)")
    # return temp_statistics


@router.get(
    "/activity", 
    response_model=List[dashboard_schemas.ActivityData],
    summary="Get activity timeline",
    description="""
    Retrieve activity timeline data for the admin dashboard.
    Shows interview activity over time.
    Only accessible to admin users.
    """,
    response_description="Activity timeline data",
    responses={
        200: {"description": "Success"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Admin privileges required"}
    }
)
async def get_activity_timeline(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
    time_range: str = Query(
        "month", 
        description="Time range for timeline", 
        pattern="^(week|month|quarter|year)$"
    ),
    group_by: str = Query(
        "day", 
        description="Grouping interval", 
        pattern="^(day|week|month)$"
    )
) -> List[dashboard_schemas.ActivityData]:
    """
    Get activity timeline for visualization.
    
    Parameters:
    - time_range: Time period for data (week, month, quarter, year)
    - group_by: Grouping interval (day, week, month)
    
    Returns:
    - List of ActivityData objects for timeline visualization
    """
    # Calculate date range
    today = datetime.utcnow()
    if time_range == "week":
        start_date = today - timedelta(days=7)
    elif time_range == "month":
        start_date = today - timedelta(days=30)
    elif time_range == "quarter":
        start_date = today - timedelta(days=90)
    else:  # year
        start_date = today - timedelta(days=365)
    
    # Construct SQL query based on grouping
    # Use strftime for SQLite compatibility
    if group_by == "day":
        # date_trunc = func.date_trunc('day', models.Interview.created_at)
        date_trunc = func.strftime('%Y-%m-%d', models.Interview.created_at)
    elif group_by == "week":
        # date_trunc = func.date_trunc('week', models.Interview.created_at)
        # Note: %W starts week on Monday, %U starts on Sunday. date_trunc behavior might vary.
        date_trunc = func.strftime('%Y-%W', models.Interview.created_at) 
    else:  # month
        # date_trunc = func.date_trunc('month', models.Interview.created_at)
        date_trunc = func.strftime('%Y-%m', models.Interview.created_at)
    
    # Get interview counts by date
    activity_data = db.query(
        date_trunc.label('date'), # Use the strftime result directly
        func.count(models.Interview.id).label('count')
    ).filter(
        models.Interview.created_at >= start_date
    ).group_by(
        date_trunc # Group by the strftime result
    ).order_by(
        date_trunc # Order by the strftime result
    ).all()
    
    # Format results
    result = [
        dashboard_schemas.ActivityData(
            date=data.date, # Already formatted by strftime
            count=data.count
        )
        for data in activity_data
    ]
    
    # Fill in missing dates with zero counts
    if not result:
        result = []
    
    logger.info(f"Activity timeline retrieved by admin {current_user.id}")
    return result


@router.get(
    "/user-activity/{user_id}", 
    response_model=dashboard_schemas.UserActivityStats,
    summary="Get user activity statistics",
    description="""
    Retrieve activity statistics for a specific user.
    Shows interview participation and completion rates.
    Only accessible to admin users.
    """,
    response_description="User activity statistics",
    responses={
        200: {"description": "Success"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Admin privileges required"},
        404: {"description": "User not found"}
    }
)
async def get_user_activity(
    user_id: int = Path(..., description="User ID", ge=1),
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser)
) -> dashboard_schemas.UserActivityStats:
    """
    Get activity statistics for a specific user.
    
    Parameters:
    - user_id: ID of the user to get statistics for
    
    Returns:
    - UserActivityStats object with user activity metrics
    
    Raises:
    - HTTPException 404: If user not found
    """
    # Verify user exists
    user = crud.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get interview statistics
    total_interviews = db.query(func.count(models.Interview.id)).filter(
        models.Interview.employee_id == user_id
    ).scalar()
    
    completed_interviews = db.query(func.count(models.Interview.id)).filter(
        models.Interview.employee_id == user_id,
        models.Interview.status == "completed"
    ).scalar()
    
    in_progress_interviews = db.query(func.count(models.Interview.id)).filter(
        models.Interview.employee_id == user_id,
        models.Interview.status == "in_progress"
    ).scalar()
    
    # Calculate completion rate
    if total_interviews > 0:
        completion_rate = completed_interviews / total_interviews * 100
    else:
        completion_rate = 0
    
    # Get average completion time for completed interviews
    avg_completion_time = None
    if completed_interviews > 0:
        completed_interview_data = db.query(
            models.Interview.created_at,
            models.Interview.completed_at
        ).filter(
            models.Interview.employee_id == user_id,
            models.Interview.status == "completed",
            models.Interview.completed_at.isnot(None)
        ).all()
        
        if completed_interview_data:
            total_minutes = 0
            count = 0
            for interview in completed_interview_data:
                if interview.completed_at and interview.created_at:
                    duration = interview.completed_at - interview.created_at
                    total_minutes += duration.total_seconds() / 60
                    count += 1
            
            if count > 0:
                avg_completion_time = round(total_minutes / count, 2)
    
    # Get message count
    total_messages = 0
    if hasattr(models, 'Message'):
        total_messages = db.query(func.count(models.Message.id)).join(
            models.Interview
        ).filter(
            models.Interview.employee_id == user_id
        ).scalar()
    
    # Construct response
    user_stats = dashboard_schemas.UserActivityStats(
        user_id=user_id,
        full_name=user.full_name,
        email=user.email,
        total_interviews=total_interviews,
        completed_interviews=completed_interviews,
        in_progress_interviews=in_progress_interviews,
        completion_rate=round(completion_rate, 2),
        avg_completion_time_minutes=avg_completion_time,
        total_messages=total_messages
    )
    
    logger.info(f"User activity statistics for user {user_id} retrieved by admin {current_user.id}")
    return user_stats


@router.get(
    "/insights", 
    response_model=dashboard_schemas.InsightsData,
    summary="Get interview insights",
    description="""
    Retrieve insights and trends from completed interviews.
    Shows common themes and satisfaction scores.
    Only accessible to admin users.
    """,
    response_description="Interview insights data",
    responses={
        200: {"description": "Success"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Admin privileges required"}
    }
)
async def get_interview_insights(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
    time_range: str = Query(
        "all", 
        description="Time range for insights", 
        pattern="^(month|quarter|year|all)$"
    )
) -> dashboard_schemas.InsightsData:
    """
    Get insights from completed interviews.
    
    Parameters:
    - time_range: Time period for data (month, quarter, year, all)
    
    Returns:
    - InsightsData object with common themes and satisfaction metrics
    """
    # Calculate date range
    today = datetime.utcnow()
    if time_range == "month":
        start_date = today - timedelta(days=30)
    elif time_range == "quarter":
        start_date = today - timedelta(days=90)
    elif time_range == "year":
        start_date = today - timedelta(days=365)
    else:  # all
        start_date = datetime.min
    
    # Get completed interviews in date range
    completed_interviews = db.query(models.Interview).filter(
        models.Interview.status == "completed",
        models.Interview.completed_at >= start_date
    ).all()
    
    interview_ids = [interview.id for interview in completed_interviews]
    
    # Get reports for these interviews
    reports = []
    if hasattr(models, 'Report'):
        reports = db.query(models.Report).filter(
            models.Report.interview_id.in_(interview_ids)
        ).all()
    
    # Analyze reports for themes and satisfaction
    common_themes = {}
    satisfaction_scores = []
    
    for report in reports:
        # Extract common themes (implementation depends on report structure)
        if hasattr(report, 'themes') and report.themes:
            for theme in report.themes:
                common_themes[theme] = common_themes.get(theme, 0) + 1
        
        # Extract satisfaction scores
        if hasattr(report, 'satisfaction_score') and report.satisfaction_score is not None:
            satisfaction_scores.append(report.satisfaction_score)
    
    # Sort themes by frequency
    sorted_themes = sorted(
        [{"theme": k, "count": v} for k, v in common_themes.items()],
        key=lambda x: x["count"],
        reverse=True
    )
    
    # Calculate average satisfaction if scores exist
    avg_satisfaction = None
    if satisfaction_scores:
        avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores)
    
    # Construct response
    insights = dashboard_schemas.InsightsData(
        total_analyzed=len(reports),
        time_range=time_range,
        common_themes=sorted_themes[:10],  # Top 10 themes
        avg_satisfaction=avg_satisfaction
    )
    
    logger.info(f"Interview insights retrieved by admin {current_user.id}")
    return insights


@router.get(
    "/export-data", 
    response_model=dashboard_schemas.ExportData,
    summary="Export dashboard data",
    description="""
    Export dashboard data for reporting purposes.
    Returns aggregated interview data in a structured format.
    Only accessible to admin users.
    """,
    response_description="Exported dashboard data",
    responses={
        200: {"description": "Success"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Admin privileges required"}
    }
)
async def export_dashboard_data(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_superuser),
    start_date: Optional[datetime] = Query(
        None, 
        description="Start date for export (ISO format)"
    ),
    end_date: Optional[datetime] = Query(
        None, 
        description="End date for export (ISO format)"
    ),
    format: str = Query(
        "json", 
        description="Export format", 
        pattern="^(json|csv)$"
    )
) -> dashboard_schemas.ExportData:
    """
    Export dashboard data for reporting.
    
    Parameters:
    - start_date: Start date for data export (optional)
    - end_date: End date for data export (optional)
    - format: Export format (json or csv)
    
    Returns:
    - ExportData object with structured data ready for export
    """
    # Set default date range if not provided
    if start_date is None:
        start_date = datetime.utcnow() - timedelta(days=30)
    
    if end_date is None:
        end_date = datetime.utcnow()
    
    # Query interviews in date range
    interviews = db.query(models.Interview).filter(
        models.Interview.created_at >= start_date,
        models.Interview.created_at <= end_date
    ).all()
    
    # Format interview data for export
    interview_data = []
    for interview in interviews:
        employee = crud.get_user(db, user_id=interview.employee_id)
        
        # Get interview report if available
        report = None
        if hasattr(models, 'Report'):
             report = db.query(models.Report).filter(
                models.Report.interview_id == interview.id
             ).first()
        
        # Get message count
        message_count = 0
        if hasattr(models, 'Message'):
            message_count = db.query(func.count(models.Message.id)).filter(
                models.Message.interview_id == interview.id
            ).scalar()
        
        # Format interview data
        interview_data.append({
            "id": interview.id,
            "employee_id": interview.employee_id,
            "employee_name": employee.full_name if employee else "Unknown",
            "employee_email": employee.email if employee else "Unknown",
            "status": interview.status,
            "created_at": interview.created_at.isoformat() if interview.created_at else None,
            "completed_at": interview.completed_at.isoformat() if interview.completed_at else None,
            "message_count": message_count,
            "has_report": report is not None,
            "interview_type": interview.interview_type if hasattr(interview, 'interview_type') else None 
        })
    
    # Generate export metadata
    export_data = dashboard_schemas.ExportData(
        generated_at=datetime.utcnow(),
        start_date=start_date,
        end_date=end_date,
        format=format,
        total_records=len(interview_data),
        data=interview_data
    )
    
    logger.info(f"Dashboard data exported by admin {current_user.id}")
    return export_data 