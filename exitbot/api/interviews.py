from datetime import datetime, date
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session

from exitbot.database.crud import (
    get_all_interviews, 
    get_interview_by_id, 
    update_interview_status,
    get_interviews_by_department
)
from exitbot.database.database import get_db
from exitbot.database.models import User, Interview
from exitbot.api.auth import get_current_user

router = APIRouter(prefix="/api/interviews", tags=["interviews"])

@router.get("/")
async def list_interviews(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    department: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all exit interviews with optional filtering
    """
    if not current_user.is_hr and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access interview data")
    
    interviews = get_all_interviews(
        db, 
        skip=skip, 
        limit=limit,
        status=status,
        department=department,
        start_date=start_date,
        end_date=end_date
    )
    
    # Format the interviews for the API response
    results = []
    for interview in interviews:
        # Calculate average sentiment
        sentiments = [float(r.sentiment) for r in interview.responses if r.sentiment is not None]
        avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else None
        
        # Extract exit reason if available
        exit_reason = None
        for response in interview.responses:
            if "reason" in response.question_text.lower() and "leaving" in response.question_text.lower():
                exit_reason = response.employee_message
                if len(exit_reason) > 100:
                    exit_reason = exit_reason[:100] + "..."
                break
        
        # Format the interview data
        interview_data = {
            "id": interview.id,
            "employee_id": interview.employee_id,
            "department": interview.department,
            "status": interview.status,
            "created_at": interview.created_at.isoformat(),
            "completed_at": interview.completed_at.isoformat() if interview.completed_at else None,
            "sentiment_score": avg_sentiment,
            "exit_reason": exit_reason,
            "response_count": len(interview.responses)
        }
        
        results.append(interview_data)
    
    return {"interviews": results, "total": len(results)}

@router.get("/{interview_id}")
async def get_interview(
    interview_id: int = Path(..., title="The ID of the interview to retrieve"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get details for a specific exit interview
    """
    if not current_user.is_hr and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access interview data")
    
    interview = get_interview_by_id(db, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Format responses
    responses = []
    for response in interview.responses:
        response_data = {
            "id": response.id,
            "question": response.question_text,
            "answer": response.employee_message,
            "bot_response": response.bot_response,
            "sentiment": float(response.sentiment) if response.sentiment is not None else None,
            "created_at": response.created_at.isoformat()
        }
        responses.append(response_data)
    
    # Sort responses by creation time
    responses.sort(key=lambda x: x["created_at"])
    
    # Format the interview data
    interview_data = {
        "id": interview.id,
        "employee_id": interview.employee_id,
        "department": interview.department,
        "status": interview.status,
        "created_at": interview.created_at.isoformat(),
        "completed_at": interview.completed_at.isoformat() if interview.completed_at else None,
        "responses": responses
    }
    
    return interview_data

@router.put("/{interview_id}/status")
async def update_status(
    interview_id: int,
    status: str = Query(..., description="New status (in_progress, completed, archived)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the status of an exit interview
    """
    if not current_user.is_hr and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to update interview status")
    
    # Validate status
    valid_statuses = ["in_progress", "completed", "archived"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
    
    # Update the interview status
    updated = update_interview_status(db, interview_id, status)
    if not updated:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    return {"status": "success", "message": f"Interview {interview_id} status updated to {status}"}

@router.get("/departments")
async def get_departments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a list of all departments with interviews
    """
    if not current_user.is_hr and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this information")
    
    # Get all interviews
    interviews = get_all_interviews(db, skip=0, limit=1000)
    
    # Extract unique departments
    departments = set()
    for interview in interviews:
        if interview.department:
            departments.add(interview.department)
    
    # Sort departments alphabetically
    sorted_departments = sorted(list(departments))
    
    return {"departments": sorted_departments} 