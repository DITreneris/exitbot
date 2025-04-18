"""
Endpoints for managing and conducting interviews.
"""
from typing import List, Optional, Any, Dict
import logging
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status, BackgroundTasks
from sqlalchemy.orm import Session

from ...db import crud
from ...db import models
from ...schemas.interview import (
    Interview, 
    InterviewCreate, 
    InterviewUpdate, 
    InterviewStatus, 
    InterviewList, 
    InterviewWithInitialMessage,
    MessageRole
)
from ...schemas.response import Response as ResponseSchema, ResponseCreate
from ...schemas.message import Message as MessageSchema, MessageCreate, MessageRole
from ...schemas.report import Report
from ...services.reporting import ReportingService
from .. import deps
from ...core.config import settings
from ...core.interview_questions import get_question_by_order, PREDEFINED_QUESTIONS

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=InterviewList)
async def list_interviews(
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    skip: int = Query(0, description="Number of items to skip for pagination"),
    limit: int = Query(100, description="Maximum number of items to return"),
    status: Optional[str] = Query(None, description="Filter by interview status")
) -> InterviewList:
    """
    List all interviews accessible to the current user.
    
    - Admin users can see all interviews
    - Regular users can only see their own interviews
    
    Parameters:
    - skip: Number of items to skip for pagination
    - limit: Maximum number of items to return
    - status: Optional filter by interview status
    
    Returns:
    - InterviewList object containing total count and items
    
    Raises:
    - HTTPException 403: If user doesn't have sufficient permissions
    """
    if current_user.is_admin:
        interviews = crud.get_all_interviews(db, skip=skip, limit=limit)
        total_count = len(interviews)
    else:
        interviews = crud.get_interviews_by_employee(db, employee_id=current_user.id)
        total_count = len(interviews)
    
    return InterviewList(total=total_count, items=interviews)


@router.post("/", response_model=InterviewWithInitialMessage, status_code=status.HTTP_201_CREATED)
async def create_interview(
    *,
    db: Session = Depends(deps.get_db),
    interview_in: InterviewCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> InterviewWithInitialMessage:
    """
    Create a new interview and generate the initial bot message.
    
    Admin users can create interviews for any user, while regular users can only
    create interviews for themselves.
    
    Parameters:
    - interview_in: Interview creation data
    
    Returns:
    - InterviewWithInitialMessage object including the first message
    
    Raises:
    - HTTPException 400: If trying to create interview for another user without permissions
    - HTTPException 404: If the specified employee does not exist
    - HTTPException 500: If fetching the initial question or DB operation fails
    """
    # Check if the user creating the interview is an admin or the employee themselves
    if not current_user.is_admin and interview_in.employee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to create an interview for this employee",
        )
    
    # Check if employee exists
    employee = crud.get_user(db, user_id=interview_in.employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )
    
    # Create interview
    interview = crud.create_interview(
        db=db, 
        employee_id=interview_in.employee_id, 
        title=interview_in.title,
        exit_date=interview_in.exit_date, 
        status=InterviewStatus.IN_PROGRESS, # <-- Start in progress
        created_by_id=current_user.id
    )
    
    logger.info(
        f"Interview {interview.id} created by user {current_user.id} "
        f"for employee {interview.employee_id}"
    )
    
    # --- Get the first predefined question ---
    initial_message_content = ""
    initial_response_db = None
    initial_message_schema = None
    first_question_id = None
    
    try:
        # Get the first predefined question (order=1)
        first_question = get_question_by_order(1)

        if not first_question:
            logger.error(f"Could not retrieve the first predefined question for interview {interview.id}")
            raise ValueError("Failed to get the first predefined question. Ensure questions are defined.")

        initial_message_content = first_question['text']
        first_question_id = first_question['id']

        # Store the initial question as a Response entry
        response_data = {
            "interview_id": interview.id,
            "question_id": first_question_id, # Store the ID of the predefined question
            "employee_message": None, # No user message yet
            "bot_response": initial_message_content,
            "sentiment": None
        }
        initial_response_db = crud.create_response(db, response_data=response_data)
        logger.info(f"Initial question (ID: {first_question_id}) stored for interview {interview.id}")
        
        # Convert the DB Response to a Message schema for the return object
        initial_message_schema = MessageSchema(
            id=initial_response_db.id, # Use response ID as message ID
            interview_id=interview.id,
            role=MessageRole.ASSISTANT,
            content=initial_response_db.bot_response,
            created_at=initial_response_db.created_at
        )
        
    except Exception as e:
        logger.error(f"Failed to create interview {interview.id} with initial question: {str(e)}", exc_info=True)
        # Clean up the created interview if initialization failed? Maybe not, allow retry later?
        # For now, just raise the error so the client knows.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize interview conversation: {str(e)}"
        )

    # Construct the final response object
    # We need to manually construct it because the default `from_attributes` won't know
    # how to map the interview object and the separate initial_message schema.
    response_data = interview.__dict__ # Get interview fields
    response_data['initial_message'] = initial_message_schema # Add the message
    response_data['responses'] = [] # Ensure responses list is present (empty initially)
    
    return InterviewWithInitialMessage(**response_data)


@router.get("/{interview_id}", response_model=Interview)
async def get_interview(
    *,
    db: Session = Depends(deps.get_db),
    interview_id: int = Path(..., title="The ID of the interview to get", ge=1),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Interview:
    """
    Get a specific interview by ID.
    
    Admin users can access any interview, while regular users can only
    access their own interviews.
    
    Parameters:
    - interview_id: The ID of the interview to retrieve
    
    Returns:
    - Interview object
    
    Raises:
    - HTTPException 404: If interview not found
    - HTTPException 403: If user doesn't have access to this interview
    """
    interview = crud.get_interview(db=db, interview_id=interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Interview not found"
        )
        
    if not current_user.is_admin and interview.employee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not enough permissions to access this interview"
        )
        
    return interview


@router.put("/{interview_id}", response_model=Interview)
async def update_interview(
    *,
    db: Session = Depends(deps.get_db),
    interview_id: int = Path(..., title="The ID of the interview to update", ge=1),
    interview_in: InterviewUpdate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Interview:
    """
    Update an interview.
    
    Admin users can update any interview, while regular users can only
    update their own interviews.
    
    Parameters:
    - interview_id: The ID of the interview to update
    - interview_in: Updated interview data
    
    Returns:
    - Updated Interview object
    
    Raises:
    - HTTPException 404: If interview not found
    - HTTPException 403: If user doesn't have permission to update this interview
    """
    interview = crud.get_interview(db=db, interview_id=interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Interview not found"
        )
        
    if not current_user.is_admin and interview.employee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not enough permissions to modify this interview"
        )
    
    # If status is being changed to completed, record completion time
    if interview_in.status == "completed" and interview.status != "completed":
        interview_in.completed_at = datetime.utcnow()
    
    # Use the new general update function
    update_data = interview_in.model_dump(exclude_unset=True) # Get only provided fields
    
    # Call the general CRUD update function
    updated_interview = crud.update_interview(db=db, db_interview=interview, interview_in=update_data)

    logger.info(f"Interview {interview_id} updated by user {current_user.id}")
    return updated_interview # Return the result from the update function


@router.delete("/{interview_id}", response_model=Interview)
async def delete_interview(
    *,
    db: Session = Depends(deps.get_db),
    interview_id: int = Path(..., title="The ID of the interview to delete", ge=1),
    current_user: models.User = Depends(deps.get_current_active_superuser),
) -> Interview:
    """
    Delete an interview.
    
    Only admin users can delete interviews.
    
    Parameters:
    - interview_id: The ID of the interview to delete
    
    Returns:
    - Deleted Interview object
    
    Raises:
    - HTTPException 404: If interview not found
    - HTTPException 403: If user doesn't have permission (handled by dependency)
    """
    interview = crud.get_interview(db=db, interview_id=interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Interview not found"
        )
        
    db.delete(interview)
    db.commit()
    logger.info(f"Interview {interview_id} deleted by admin {current_user.id}")
    return interview


@router.post("/{interview_id}/messages", response_model=MessageSchema)
async def send_message(
    *,
    db: Session = Depends(deps.get_db),
    interview_id: int = Path(..., title="The ID of the interview", ge=1),
    message_in: MessageCreate,
    current_user: models.User = Depends(deps.get_current_active_user),
) -> MessageSchema:
    """
    Process the user's message and return the next predefined question or end the interview.

    Parameters:
    - interview_id: The ID of the interview
    - message_in: Message content from the user

    Returns:
    - MessageSchema object with the next question or concluding message.

    Raises:
    - HTTPException 404: If interview not found
    - HTTPException 403: If user doesn't have access to this interview
    - HTTPException 400: If interview is not in progress
    - HTTPException 500: If there's an error processing the message or DB operation fails
    """
    interview = crud.get_interview(db=db, interview_id=interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Interview not found"
        )

    if not current_user.is_admin and interview.employee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not enough permissions to participate in this interview"
        )

    # Use the Enum member for comparison
    if interview.status != InterviewStatus.IN_PROGRESS: 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot send messages to an interview with status '{interview.status}'"
        )

    # --- Start of Correct Logic ---
    try:
        # Get previous responses to determine which question is next
        previous_responses = crud.get_responses_by_interview(
            db=db, interview_id=interview_id
        )
        # The order of the next question is the number of previous bot responses + 1
        # (or simply the total number of responses if the first was just the bot)
        next_question_order = len(previous_responses) + 1

        next_question = get_question_by_order(next_question_order)

        if next_question:
            # There's another question to ask
            bot_response_content = next_question['text']
            next_question_id = next_question['id']

            # Store user's message and the next bot question together
            new_response = crud.create_response(db, response_data={
                "interview_id": interview_id,
                "question_id": next_question_id, # ID of the question being asked now
                "employee_message": message_in.content, # User's answer to the *previous* question
                "bot_response": bot_response_content,
                "sentiment": None # Sentiment analysis can be done later
            })
            
            logger.info(f"Stored response for question {next_question_id-1} and asking question {next_question_id} for interview {interview_id}")

            # Return the next question
            return MessageSchema(
                id=new_response.id, # Use the new response ID
                interview_id=interview_id,
                role=MessageRole.ASSISTANT,
                content=bot_response_content,
                created_at=new_response.created_at 
            )
        else:
            # No more questions, end the interview
            concluding_message = "Thank you for completing the exit interview. Your feedback is valuable."
            
            # Determine the ID of the last question asked by looking at previous responses
            last_question_id = None
            if previous_responses:
                 # Find the question_id from the last response entry that had one
                 for resp in reversed(previous_responses):
                     if resp.question_id is not None:
                         last_question_id = resp.question_id
                         break
            
            # Store the final user message along with the concluding bot message
            final_response = crud.create_response(db, response_data={
                "interview_id": interview_id,
                 # Link this final answer to the last actual question asked
                "question_id": last_question_id, 
                "employee_message": message_in.content, 
                "bot_response": concluding_message,
                "sentiment": None
            })

            # Update interview status to completed
            crud.update_interview(
                db=db, 
                db_interview=interview, 
                # Use Enum member for status
                interview_in={"status": InterviewStatus.COMPLETED, "completed_at": datetime.utcnow()} 
            )
            
            logger.info(f"Interview {interview_id} completed.")

            # Return the concluding message
            return MessageSchema(
                id=final_response.id, # Use the final response ID
                interview_id=interview_id,
                role=MessageRole.ASSISTANT,
                content=concluding_message,
                created_at=final_response.created_at
            )

    except Exception as e:
        # Catch potential errors during question retrieval or DB operations
        logger.error(f"Error processing message for interview {interview_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing your message"
        )
    # --- End of Correct Logic ---


@router.get("/{interview_id}/messages", response_model=List[MessageSchema])
async def get_interview_messages(
    *,
    db: Session = Depends(deps.get_db),
    interview_id: int = Path(..., title="The ID of the interview", ge=1),
    current_user: models.User = Depends(deps.get_current_active_user),
    skip: int = Query(0, description="Number of items to skip for pagination"),
    limit: int = Query(100, description="Maximum number of items to return"),
) -> List[MessageSchema]:
    """
    Get all messages for a specific interview.
    
    Admin users can access any interview messages, while regular users can only
    access messages from their own interviews.
    
    Parameters:
    - interview_id: The ID of the interview
    - skip: Number of messages to skip for pagination
    - limit: Maximum number of messages to return
    
    Returns:
    - List of Message objects
    
    Raises:
    - HTTPException 404: If interview not found
    - HTTPException 403: If user doesn't have access to this interview
    """
    interview = crud.get_interview(db=db, interview_id=interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Interview not found"
        )
        
    if not current_user.is_admin and interview.employee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not enough permissions to access messages for this interview"
        )
        
    # Fetch responses 
    responses = crud.get_responses_by_interview(db, interview_id=interview_id)
    
    # Sort responses by creation time BEFORE processing
    responses.sort(key=lambda r: r.created_at)
    
    messages = []
    message_id_counter = 1 
    for resp in responses: # Iterate through sorted responses
        # Add user message if it exists
        if resp.employee_message:
             messages.append(MessageSchema(
                 id=message_id_counter, 
                 interview_id=interview_id, 
                 role="user", 
                 content=resp.employee_message, 
                 created_at=resp.created_at
             ))
             message_id_counter += 1
        # Add bot response if it exists, slightly adjusting timestamp for ordering if needed
        if resp.bot_response:
             # Use a slightly later timestamp for the bot response for stable sorting
             # This ensures assistant message comes after user message from the same Response entry
             bot_created_at = resp.created_at + timedelta(milliseconds=1)
             messages.append(MessageSchema(
                 id=message_id_counter, 
                 interview_id=interview_id, 
                 role="assistant", 
                 content=resp.bot_response, 
                 created_at=bot_created_at
             ))
             message_id_counter += 1
    
    # messages.sort(key=lambda m: m.created_at) # This sort is redundant now
    
    return messages[skip : skip + limit]


@router.post("/{interview_id}/reports", response_model=Report)
async def generate_report(
    *,
    db: Session = Depends(deps.get_db),
    interview_id: int = Path(..., title="The ID of the interview", ge=1),
    current_user: models.User = Depends(deps.get_current_active_user),
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Generate a report for a completed interview.
    
    This endpoint will generate a summary and analysis of the interview.
    Admin users can generate reports for any completed interview,
    while regular users can only generate reports for their own completed interviews.
    
    Parameters:
    - interview_id: The ID of the interview to generate a report for
    
    Returns:
    - Report object with summary and analysis
    
    Raises:
    - HTTPException 404: If interview not found
    - HTTPException 403: If user doesn't have access to this interview
    - HTTPException 400: If interview is not completed
    """
    interview = crud.get_interview(db=db, interview_id=interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Interview not found"
        )
        
    if not current_user.is_admin and interview.employee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not enough permissions to generate a report for this interview"
        )
    
    if interview.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot generate report for an interview that is not completed"
        )
    
    # Check if report already exists
    existing_report = crud.report.get_by_interview_id(db=db, interview_id=interview_id)
    if existing_report:
        return existing_report
    
    # Update interview status to indicate report generation
    # crud.update_interview_status(db, interview_id=interview_id, status="generating_report") # Removed invalid status update

    # Generate report  
    try:
        report = ReportingService.generate_interview_summary(db=db, interview_id=interview_id)
        logger.info(f"Report generated for interview {interview_id}")
        return report
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating report"
        )


@router.get("/{interview_id}/reports", response_model=Report)
async def get_report(
    *,
    db: Session = Depends(deps.get_db),
    interview_id: int = Path(..., title="The ID of the interview", ge=1),
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Report:
    """
    Get the report for a specific interview.
    
    Admin users can access any interview report, while regular users can only
    access reports for their own interviews.
    
    Parameters:
    - interview_id: The ID of the interview
    
    Returns:
    - Report object
    
    Raises:
    - HTTPException 404: If interview or report not found
    - HTTPException 403: If user doesn't have access to this interview
    """
    interview = crud.get_interview(db=db, interview_id=interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Interview not found"
        )
        
    if not current_user.is_admin and interview.employee_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Not enough permissions to access the report for this interview"
        )
    
    if interview.status == "completed":
         # In a real scenario, fetch the generated report from storage or DB
         report_data = {
              "id": 0, # Placeholder ID
              "interview_id": interview_id,
              "summary": "Report summary placeholder.",
              "sentiment_score": 0.5, # Placeholder
              "key_topics": ["placeholder topic"], # Placeholder - Note: Report schema uses 'themes' not 'key_topics'
              "themes": [{"name": "placeholder_theme", "details": "placeholder details"}], # Added placeholder themes
              "recommendations": ["placeholder recommendation"], # Placeholder
              "created_at": datetime.utcnow(), # Placeholder - Note: Report schema uses generated_at
              "generated_at": datetime.utcnow(), # Added placeholder generated_at
              "report_url": None # Placeholder
         }
         return Report(**report_data)
    elif interview.status == "generating_report":
        raise HTTPException(
            status_code=status.HTTP_202_ACCEPTED,
            detail="Report generation still in progress."
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Report not found for this interview. Ensure the interview is completed and report generation has been triggered."
        ) 