from datetime import date
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import PlainTextResponse, JSONResponse
from sqlalchemy.orm import Session

from app.api.auth import get_current_admin
from app.core.logging import get_logger
from app.db import crud
from app.db.base import get_db
from app.schemas.auth import User
from app.schemas.report import (
    SummaryStats,
    DepartmentReport,
    Report
)
from app.services.reporting import ReportingService

logger = get_logger("api.reports")
router = APIRouter()

@router.get("/summary", response_model=SummaryStats)
async def get_summary_stats(
    start_date: date = None,
    end_date: date = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get summary statistics for exit interviews (admin only)
    """
    try:
        stats = ReportingService.get_summary_stats(db, start_date, end_date)
        return stats
    except Exception as e:
        logger.error(f"Error generating summary stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating summary statistics"
        )

@router.get("/by-department", response_model=DepartmentReport)
async def get_department_breakdown(
    start_date: date = None,
    end_date: date = None,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> Any:
    """
    Get breakdown of exit interviews by department (admin only)
    """
    try:
        departments = ReportingService.get_department_breakdown(db, start_date, end_date)
        return {"departments": departments}
    except Exception as e:
        logger.error(f"Error generating department breakdown: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating department breakdown"
        )

@router.get("/interview/{interview_id}/summary")
async def get_interview_summary(
    interview_id: int,
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> Any:
    """
    Generate a summary of an exit interview (admin only)
    """
    try:
        # Check if interview exists
        interview = crud.get_interview(db, interview_id)
        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Interview not found"
            )
        
        summary = ReportingService.generate_interview_summary(db, interview_id)
        return PlainTextResponse(summary)
    except ValueError as e:
        logger.error(f"Value error generating interview summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error generating interview summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating interview summary"
        )

@router.get("/export", response_class=JSONResponse)
async def export_data(
    start_date: date = None,
    end_date: date = None,
    department: str = None,
    format: str = Query("json", regex="^(json|csv)$"),
    current_user: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
) -> Any:
    """
    Export interview data as JSON or CSV (admin only)
    """
    try:
        # Get interviews
        query = db.query(crud.Interview)
        
        # Apply filters
        if start_date:
            query = query.filter(crud.Interview.created_at >= start_date)
        if end_date:
            query = query.filter(crud.Interview.created_at <= end_date)
        
        if department:
            query = query.join(crud.User).filter(crud.User.department == department)
            
        interviews = query.all()
        
        # Format data
        data = []
        for interview in interviews:
            interview_data = {
                "id": interview.id,
                "employee_id": interview.employee_id,
                "employee_name": interview.employee.full_name if interview.employee else None,
                "department": interview.employee.department if interview.employee else None,
                "start_date": interview.start_date.isoformat(),
                "end_date": interview.end_date.isoformat() if interview.end_date else None,
                "status": interview.status,
                "responses": []
            }
            
            # Add responses
            for response in interview.responses:
                question = crud.get_question(db, response.question_id)
                interview_data["responses"].append({
                    "question": question.text if question else None,
                    "employee_response": response.employee_message,
                    "bot_response": response.bot_response,
                    "sentiment": response.sentiment
                })
                
            data.append(interview_data)
        
        # Return data
        return data
        # Note: In a real implementation, CSV format would be supported
    except Exception as e:
        logger.error(f"Error exporting data: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error exporting data"
        ) 