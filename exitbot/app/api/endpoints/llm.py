"""
API endpoints for LLM integration and management.
"""
import logging
from typing import Dict, List, Any

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
    BackgroundTasks,
)
from sqlalchemy.orm import Session

from ...db import models
from ...db import crud
from .. import deps
from ...core.config import settings

# from ...core.llm import get_llm_client # Commented out - likely wrong path or self-import

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/completion",
    response_model=Dict[str, Any],
    summary="Generate LLM completion",
    description="""
    Generate a text completion using the configured LLM provider.
    This endpoint is for direct interaction with the LLM without storing the conversation.
    """,
    response_description="Generated text completion",
    responses={
        200: {"description": "Success"},
        401: {"description": "Unauthorized"},
        500: {"description": "LLM service error"},
    },
)
async def generate_completion(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    prompt: str = Query(..., description="Text prompt for completion", min_length=1),
    max_tokens: int = Query(
        200, description="Maximum number of tokens to generate", ge=10, le=2000
    ),
    temperature: float = Query(0.7, description="Sampling temperature", ge=0, le=2.0),
) -> Dict[str, Any]:
    """
    Generate a text completion from the LLM.

    Parameters:
    - prompt: Text prompt to generate completion for
    - max_tokens: Maximum number of tokens to generate
    - temperature: Sampling temperature (0-2)

    Returns:
    - Generated text completion and metadata

    Raises:
    - HTTPException 500: If LLM service fails
    """
    # Commented out original logic due to missing get_llm_client
    # try:
    #     # llm_client = get_llm_client(settings.LLM_PROVIDER)
    #     response = llm_client.completion(
    #         prompt=prompt,
    #         max_tokens=max_tokens,
    #         temperature=temperature
    #     )
    #
    #     # Log completion request
    #     log_entry = models.LLMLog(
    #         user_id=current_user.id,
    #         request_type="completion",
    #         prompt=prompt,
    #         response=response,
    #         parameters={
    #             "max_tokens": max_tokens,
    #             "temperature": temperature
    #         }
    #     )
    #     db.add(log_entry)
    #     db.commit()
    #
    #     logger.info(f"LLM completion generated for user {current_user.id}")
    #     return {
    #         "completion": response,
    #         "provider": settings.LLM_PROVIDER,
    #         "model": llm_client.get_model_name()
    #     }
    # except Exception as e:
    #     logger.error(f"LLM completion failed: {str(e)}")
    #     raise HTTPException(
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #         detail=f"LLM service error: {str(e)}"
    #     )
    logger.warning(
        "LLM completion endpoint called but LLM client is missing/commented out."
    )
    return {
        "completion": "[LLM Client Missing]",
        "provider": settings.LLM_PROVIDER,
        "model": "unknown",
    }


@router.post(
    "/chat",
    response_model=Dict[str, Any],
    summary="Generate chat response",
    description="""
    Generate a response to a chat message using the configured LLM provider.
    This endpoint supports multi-turn conversation with system prompts.
    """,
    response_description="Generated chat response",
    responses={
        200: {"description": "Success"},
        401: {"description": "Unauthorized"},
        500: {"description": "LLM service error"},
    },
)
async def generate_chat_response(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    messages: List[Dict[str, str]],
    max_tokens: int = Query(
        1000, description="Maximum number of tokens to generate", ge=10, le=4000
    ),
    temperature: float = Query(0.7, description="Sampling temperature", ge=0, le=2.0),
) -> Dict[str, Any]:
    """
    Generate a response to a chat conversation.

    Parameters:
    - messages: List of message objects with 'role' and 'content'
    - max_tokens: Maximum number of tokens to generate
    - temperature: Sampling temperature (0-2)

    Returns:
    - Generated chat response and metadata

    Raises:
    - HTTPException: If LLM service fails or messages format is invalid
    """
    # Validate messages format
    for message in messages:
        if (
            not isinstance(message, dict)
            or "role" not in message
            or "content" not in message
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid message format. Each message must have 'role' and 'content'",
            )
        if message["role"] not in ["system", "user", "assistant"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role. Must be one of: system, user, assistant",
            )

    # Commented out original logic due to missing get_llm_client
    # try:
    #     # llm_client = get_llm_client(settings.LLM_PROVIDER)
    #     response = llm_client.chat_completion(...)
    #     log_entry = models.LLMLog(...)
    #     db.add(log_entry)
    #     db.commit()
    #     logger.info(...)
    #     return { ... }
    # except Exception as e:
    #     logger.error(...)
    #     raise HTTPException(...)
    logger.warning("LLM chat endpoint called but LLM client is missing/commented out.")
    return {
        "response": "[LLM Client Missing]",
        "provider": settings.LLM_PROVIDER,
        "model": "unknown",
    }


@router.post(
    "/analyze",
    response_model=Dict[str, Any],
    summary="Analyze text content",
    description="""
    Analyze text content using the configured LLM provider.
    This endpoint extracts insights, themes, and sentiment from text.
    Primarily used for interview analysis but can be used for any text.
    """,
    response_description="Analysis results",
    responses={
        200: {"description": "Success"},
        401: {"description": "Unauthorized"},
        500: {"description": "LLM service error"},
    },
)
async def analyze_text(
    *,
    db: Session = Depends(deps.get_db),
    current_user: models.User = Depends(deps.get_current_active_user),
    content: str = Query(..., description="Text content to analyze", min_length=1),
    analysis_type: str = Query(
        "general",
        description="Type of analysis to perform",
        regex="^(general|sentiment|themes|summary)$",
    ),
) -> Dict[str, Any]:
    """
    Analyze text content using LLM.

    Parameters:
    - content: Text content to analyze
    - analysis_type: Type of analysis to perform

    Returns:
    - Analysis results

    Raises:
    - HTTPException 500: If LLM service fails
    """
    # Commented out original logic due to missing get_llm_client
    # try:
    #     # llm_client = get_llm_client(settings.LLM_PROVIDER)
    #     # Prepare system prompt ...
    #     analysis_result = llm_client.analyze(...)
    #     log_entry = models.LLMLog(...)
    #     db.add(log_entry)
    #     db.commit()
    #     logger.info(...)
    #     return { ... }
    # except Exception as e:
    #     logger.error(...)
    #     raise HTTPException(...)
    logger.warning(
        "LLM analyze endpoint called but LLM client is missing/commented out."
    )
    return {
        "analysis": "[LLM Client Missing]",
        "analysis_type": analysis_type,
        "provider": settings.LLM_PROVIDER,
        "model": "unknown",
    }


@router.get(
    "/config",
    response_model=Dict[str, Any],
    summary="Get LLM configuration",
    description="""
    Retrieve information about the current LLM configuration.
    This includes the provider, model, and available models.
    """,
    response_description="LLM configuration",
    responses={200: {"description": "Success"}, 401: {"description": "Unauthorized"}},
)
async def get_llm_config(
    current_user: models.User = Depends(deps.get_current_active_user),
) -> Dict[str, Any]:
    """
    Get LLM configuration information.
    ...
    Raises:
        HTTPException 500: If LLM service error
    """
    # Commented out original logic due to missing get_llm_client
    # try:
    #     # llm_client = get_llm_client(settings.LLM_PROVIDER)
    #     config = llm_client.get_config()
    #     logger.info(...)
    #     return config
    # except Exception as e:
    #     logger.error(...)
    #     raise HTTPException(...)
    logger.warning(
        "LLM config endpoint called but LLM client is missing/commented out."
    )
    return {
        "provider": settings.LLM_PROVIDER,
        "model": "unknown",
        "status": "[LLM Client Missing]",
    }


@router.post(
    "/interview/{interview_id}/generate-report",
    response_model=Dict[str, Any],
    summary="Generate interview report",
    description="""
    Generate a detailed report for a completed interview using the LLM.
    This is an asynchronous operation that runs in the background.
    """,
    response_description="Report generation status",
    responses={
        202: {"description": "Report generation started"},
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - Not authorized for this interview"},
        404: {"description": "Interview not found"},
        409: {"description": "Report already exists or interview not completed"},
        500: {"description": "Service error"},
    },
)
async def generate_interview_report(
    *,
    db: Session = Depends(deps.get_db),
    interview_id: int = Path(..., description="The ID of the interview", ge=1),
    current_user: models.User = Depends(deps.get_current_active_user),
    background_tasks: BackgroundTasks,
) -> Dict[str, Any]:
    """
    Generate interview report using LLM in the background.
    """
    interview = crud.interview.get(db, id=interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Interview not found"
        )
    if not crud.interview.can_access_interview(
        db, user=current_user, interview=interview
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Not enough permissions"
        )
    if interview.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Interview not completed"
        )
    existing_report = crud.report.get_by_interview_id(db=db, interview_id=interview_id)
    if existing_report:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Report already exists"
        )

    # Comment out background task logic involving LLM client
    # try:
    #     # llm_client = get_llm_client(settings.LLM_PROVIDER)
    #     background_tasks.add_task(
    #         _generate_report_background, db, interview_id, None # Pass None for llm_client
    #     )
    #     logger.info(f"Report generation started for interview {interview_id}")
    #     return {"status": "Report generation started", "interview_id": interview_id}
    # except Exception as e:
    #     logger.error(f"Failed to start report generation: {str(e)}")
    #     raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to start report generation")
    logger.warning(
        "LLM generate-report endpoint called but LLM client is missing/commented out."
    )
    return {
        "status": "Report generation skipped [LLM Client Missing]",
        "interview_id": interview_id,
    }


# Comment out the entire background task function as it relies heavily on the missing client
# async def _generate_report_background(
#     db: Session, interview_id: int, llm_client: Any # Accept placeholder
# ):
#     """
#     Background task to generate the interview report.
#     """
#     # try:
#     #     # Fetch interview data
#     #     # ... crud calls ...
#     #
#     #     # Generate report using LLM
#     #     report_content = llm_client.generate_report(...)
#     #
#     #     # Save report
#     #     # ... crud calls ...
#     #     logger.info(...)
#     # except Exception as e:
#     #     logger.error(...)
#     pass # Placeholder if function definition is kept
