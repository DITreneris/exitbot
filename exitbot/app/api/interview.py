from typing import List, Any, Optional
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from exitbot.app.db.base import get_db
from exitbot.app.db.models import User, Interview, Question, Response
from exitbot.app.schemas.interview import InterviewCreate, Interview, InterviewDetail, InterviewResponse, Message
from exitbot.app.services.interview import InterviewService
from exitbot.app.db import crud
from exitbot.app.core.logging import get_logger
from exitbot.app.services.reporting import ReportingService

logger = get_logger("api.interview")
router = APIRouter()

@router.post("/start", response_model=Interview)
async def start_interview(
    interview_data: InterviewCreate,
    db: Session = Depends(get_db),
) -> Any:
    """
    Start a new exit interview
    """
    try:
        interview = InterviewService.start_interview(
            db=db,
            employee_id=interview_data.employee_id,
            exit_date=interview_data.exit_date
        )
        return interview
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting interview: {str(e)}"
        )

@router.post("/{interview_id}/message", response_model=InterviewResponse)
async def process_message(
    interview_id: int,
    message_data: Message,
    db: Session = Depends(get_db),
) -> Any:
    """
    Process a message in an exit interview
    """
    # Verify interview exists
    interview = crud.get_interview(db, interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )
    
    # Validate message belongs to this interview
    if message_data.interview_id != interview_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Message interview ID does not match URL"
        )
    
    try:
        # Process the message
        response = InterviewService.process_message(
            db=db,
            interview_id=interview_id,
            message=message_data.message,
            question_id=message_data.question_id
        )
        
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}"
        )

@router.put("/{interview_id}/complete", response_model=Interview)
async def complete_interview(
    interview_id: int,
    db: Session = Depends(get_db),
) -> Any:
    """
    Mark an interview as complete
    """
    # Verify interview exists
    interview = crud.get_interview(db, interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )
    
    try:
        # Complete the interview
        completed_interview = InterviewService.complete_interview(db, interview_id)
        
        # Invalidate any cached reports since we have new data
        try:
            ReportingService.invalidate_report_caches()
        except:
            logger.warning("Failed to invalidate report caches")
        
        return completed_interview
    except Exception as e:
        logger.error(f"Error completing interview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error completing interview"
        )

@router.get("/{interview_id}", response_model=InterviewDetail)
async def get_interview(
    interview_id: int,
    db: Session = Depends(get_db),
) -> Any:
    """
    Get details of a specific interview
    """
    # Verify interview exists
    interview = crud.get_interview(db, interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Interview not found"
        )
    
    try:
        # Get responses
        responses = crud.get_responses_by_interview(db, interview_id)
        
        # Create full response
        result = InterviewDetail(
            id=interview.id,
            employee_id=interview.employee_id,
            start_date=interview.start_date,
            end_date=interview.end_date,
            status=interview.status,
            exit_date=interview.exit_date,
            created_at=interview.created_at,
            responses=responses
        )
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting interview details: {str(e)}"
        ) 