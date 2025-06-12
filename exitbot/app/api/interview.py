from typing import Any
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from exitbot.app.db.base import get_db
from exitbot.app.db.models import Interview
from exitbot.app.schemas.interview import (
    InterviewCreate,
    InterviewDetail,
    Message,
    MessageSchema,
)
from exitbot.app.services.interview import InterviewService
from exitbot.app.db import crud
from exitbot.app.core.logging import get_logger
from exitbot.app.services.reporting import ReportingService
from exitbot.app.core import interview_questions

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
        # Create the interview
        interview = InterviewService.start_interview(
            db=db,
            employee_id=interview_data.employee_id,
            exit_date=interview_data.exit_date,
        )

        # Get the first predefined question
        first_question = interview_questions.get_question_by_order(1)
        if not first_question:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve initial question",
            )

        # Store the initial bot message
        crud.create_response(
            db=db,
            interview_id=interview.id,
            employee_message=None,
            bot_response=first_question["text"],
            question_id=first_question["id"],
        )

        # Get the updated interview
        interview = crud.get_interview(db, interview.id)

        return interview
    except Exception as e:
        logger.error(f"Error starting interview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting interview: {str(e)}",
        )


@router.post("/{interview_id}/message", response_model=MessageSchema)
async def process_message(
    interview_id: int,
    message_data: Message,
    db: Session = Depends(get_db),
) -> Any:
    """
    Process a message in an exit interview using predefined questions
    """
    try:
        # Verify interview exists
        interview = crud.get_interview(db, interview_id)
        if not interview:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found"
            )

        # Check if interview is already completed
        if interview.status == "COMPLETED":
            return {
                "content": "This interview has already been completed. Thank you for your participation.",
                "is_complete": True,
            }

        # Get previous responses to determine next question
        previous_responses = crud.get_responses_by_interview(db, interview_id)
        next_question_order = len(previous_responses) + 1

        # Get next question
        next_question = interview_questions.get_question_by_order(next_question_order)

        # Store user's response
        response_id = crud.create_response(
            db=db,
            interview_id=interview_id,
            employee_message=message_data.message,
            bot_response=next_question["text"]
            if next_question
            else "Thank you for completing the interview.",
            question_id=next_question["id"] if next_question else None,
        )

        # If no more questions, mark interview as complete
        if not next_question:
            crud.update_interview(
                db=db,
                interview_id=interview_id,
                update_dict={"status": "COMPLETED", "completed_at": datetime.now()},
            )

            # Invalidate any cached reports since we have new data
            try:
                ReportingService.invalidate_report_caches()
            except Exception:
                logger.warning("Failed to invalidate report caches")

        # Return response
        return {
            "id": response_id,
            "content": next_question["text"]
            if next_question
            else "Thank you for completing the exit interview. Your feedback is valuable to us.",
            "is_complete": next_question is None,
            "question_number": next_question_order if next_question else None,
            "total_questions": interview_questions.get_question_count(),
        }
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing message: {str(e)}",
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
            status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found"
        )

    try:
        # Complete the interview
        completed_interview = InterviewService.complete_interview(db, interview_id)

        # Invalidate any cached reports since we have new data
        try:
            ReportingService.invalidate_report_caches()
        except Exception:
            logger.warning("Failed to invalidate report caches")

        return completed_interview
    except Exception as e:
        logger.error(f"Error completing interview: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error completing interview",
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
            status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found"
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
            responses=responses,
        )

        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting interview details: {str(e)}",
        )
