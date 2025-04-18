#!/usr/bin/env python
"""
Direct ExitBot Application - simplified version with direct routing
"""
import logging
import uvicorn
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
import sys
import os
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import necessary modules
try:
    from exitbot.app.llm.factory import llm_client
    from exitbot.app.db.base import get_db
    from exitbot.app.db.models import User, Interview, Question, Response
    from exitbot.app.db import crud
    from exitbot.app.api_utils import success_response, error_response, APIException
    from exitbot.app.auth import get_current_active_user
    from exitbot.app.core.security import create_access_token
    from exitbot.app.services.interview import process_interview_message
    
    DB_AVAILABLE = True
    logger.info("All modules loaded successfully")
except ImportError as e:
    logger.warning(f"Could not import required modules: {e}")
    DB_AVAILABLE = False

# Create FastAPI app
app = FastAPI(
    title="ExitBot API",
    description="ExitBot API - AI-powered exit interview assistant",
    version="1.0.0",
    docs_url="/api/swagger",
    redoc_url="/api/redoc",
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
@app.get("/")
async def root():
    """Root endpoint with health check"""
    return success_response(
        message="ExitBot API is running",
        data={"version": "1.0.0"}
    )

@app.get("/api")
async def api_root():
    """API root endpoint - redirects to documentation"""
    return RedirectResponse(url="/api/docs")

@app.get("/api/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return success_response(message="Service is healthy")

@app.get("/api/protected")
async def protected_route(current_user: User = Depends(get_current_active_user)):
    """Protected route example"""
    return success_response(
        message="Access granted",
        data={"user": current_user.username}
    )

@app.post("/api/token")
async def login_for_access_token(
    form_data: Dict[str, str],
    db: Session = Depends(get_db)
):
    """Login endpoint to get access token"""
    try:
        user = crud.get_user_by_username(db, form_data["username"])
        if not user or not verify_password(form_data["password"], user.hashed_password):
            raise APIException(
                message="Incorrect username or password",
                status_code=status.HTTP_401_UNAUTHORIZED,
                error_code="INVALID_CREDENTIALS"
            )
        
        access_token = create_access_token(
            subject_email=user.email,
            expires_delta=timedelta(minutes=30)
        )
        
        return success_response(
            message="Login successful",
            data={
                "access_token": access_token,
                "token_type": "bearer"
            }
        )
    except KeyError:
        raise APIException(
            message="Username and password are required",
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="MISSING_CREDENTIALS"
        )

@app.post("/api/interviews/start")
async def start_interview(
    employee_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Start a new interview"""
    try:
        if not DB_AVAILABLE:
            return success_response(
                message="Interview started (mock mode)",
                data={
                    "id": 1,
                    "employee_id": employee_data.get("employee_id", 1),
                    "status": "in_progress",
                    "start_date": datetime.now().isoformat(),
                    "created_at": datetime.now().isoformat()
                }
            )
            
        employee_id = employee_data.get("employee_id")
        if not employee_id:
            raise APIException(
                message="employee_id is required",
                status_code=status.HTTP_400_BAD_REQUEST,
                error_code="MISSING_EMPLOYEE_ID"
            )
            
        interview = crud.create_interview(db, employee_id)
        
        return success_response(
            message="Interview started successfully",
            data={
                "id": interview.id,
                "employee_id": interview.employee_id,
                "status": interview.status,
                "start_date": interview.start_date.isoformat() if interview.start_date else None,
                "created_at": interview.created_at.isoformat() if interview.created_at else None
            }
        )
    except Exception as e:
        logger.error(f"Error starting interview: {str(e)}")
        raise APIException(
            message=f"Error starting interview: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="INTERVIEW_START_ERROR"
        )

@app.post("/api/interviews/{interview_id}/message")
async def process_message(
    interview_id: int,
    message_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Process a message in an interview"""
    try:
        if not DB_AVAILABLE:
            return success_response(
                message="Message processed (mock mode)",
                data={
                    "response": "Thank you for sharing. Could you tell me more about your experience?",
                    "current_question": {
                        "id": 2,
                        "text": "What did you enjoy most about working here?"
                    },
                    "is_complete": False
                }
            )
            
        message = message_data.get("message")
        if not message:
            raise APIException(
                message="message is required",
                status_code=status.HTTP_400_BAD_REQUEST,
                error_code="MISSING_MESSAGE"
            )
            
        interview = crud.get_interview(db, interview_id)
        if not interview:
            raise APIException(
                message="Interview not found",
                status_code=status.HTTP_404_NOT_FOUND,
                error_code="INTERVIEW_NOT_FOUND"
            )
            
        # Process the message and get response
        response = await process_interview_message(db, interview, message)
        
        return success_response(
            message="Message processed successfully",
            data=response
        )
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise APIException(
            message=f"Error processing message: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="MESSAGE_PROCESSING_ERROR"
        )

# Error handlers
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return error_response(
        message="An unexpected error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="INTERNAL_SERVER_ERROR",
        details={"error": str(exc)}
    )

if __name__ == "__main__":
    uvicorn.run("direct_app:app", host="0.0.0.0", port=8000, reload=True) 