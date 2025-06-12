#!/usr/bin/env python
"""
Direct app to bypass FastAPI and run the core logic.
"""
# Remove unused HTTPException
# from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi import FastAPI, Depends, Request, Form

# Remove unused HTMLResponse
# from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.responses import RedirectResponse, JSONResponse

# Remove unused sys
# import sys
# Remove unused os
# import os
from datetime import datetime, timedelta

# Remove unused List, Optional
# from typing import List, Optional, Dict, Any
from typing import Dict, Any

# Remove unused json
# import json
from exitbot.app.core.security import verify_password

# Remove unused llm_client
# from exitbot.app.llm.factory import llm_client
from exitbot.app.db.base import SessionLocal

# Remove unused Interview, Question, Response
# from exitbot.app.db.models import Interview, Question, Response, User
from exitbot.app.db.models import User
from exitbot.app.db import crud
from fastapi.middleware.cors import CORSMiddleware
from exitbot.app.api_utils import (
    success_response,
    error_response,
    APIException,
)

import logging
import uvicorn
from fastapi import status
from sqlalchemy.orm import Session

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import necessary modules
try:
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
    return success_response(message="ExitBot API is running", data={"version": "1.0.0"})


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
        message="Access granted", data={"user": current_user.username}
    )


@app.post("/api/token")
async def login_for_access_token(request: Request, db: Session = Depends(SessionLocal)):
    """Login endpoint to get access token"""
    try:
        form_data = await request.form()
        username = form_data.get("username", "")
        password = form_data.get("password", "")
        
        if not username or not password:
            raise APIException(
                message="Username and password are required",
                status_code=status.HTTP_400_BAD_REQUEST,
                error_code="MISSING_CREDENTIALS",
            )
            
        user = crud.get_user_by_username(db, username)
        if not user or not verify_password(password, user.hashed_password):
            raise APIException(
                message="Incorrect username or password",
                status_code=status.HTTP_401_UNAUTHORIZED,
                error_code="INVALID_CREDENTIALS",
            )

        access_token = create_access_token(
            subject_email=user.email, expires_delta=timedelta(minutes=30)
        )

        return success_response(
            message="Login successful",
            data={"access_token": access_token, "token_type": "bearer"},
        )
    except APIException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise APIException(
            message="Login failed",
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="LOGIN_FAILED",
        )


@app.post("/api/auth/login")
async def login_for_access_token_auth(request: Request, db: Session = Depends(SessionLocal)):
    """Login endpoint to get access token (compatibility with frontend)"""
    try:
        form_data = await request.form()
        username = form_data.get("username", "")
        password = form_data.get("password", "")
        
        if not username or not password:
            raise APIException(
                message="Username and password are required",
                status_code=status.HTTP_400_BAD_REQUEST,
                error_code="MISSING_CREDENTIALS",
            )
            
        user = crud.get_user_by_username(db, username)
        if not user or not verify_password(password, user.hashed_password):
            raise APIException(
                message="Incorrect username or password",
                status_code=status.HTTP_401_UNAUTHORIZED,
                error_code="INVALID_CREDENTIALS",
            )

        access_token = create_access_token(
            subject_email=user.email, expires_delta=timedelta(minutes=30)
        )

        return {
            "access_token": access_token, 
            "token_type": "bearer"
        }
    except APIException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise APIException(
            message="Login failed",
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="LOGIN_FAILED",
        )


@app.post("/api/login_basic")
async def login_basic(request: Request):
    """Very basic login endpoint that directly processes the raw request"""
    try:
        # Get the raw body content and log it for debugging
        body = await request.body()
        body_str = body.decode('utf-8')
        logger.info(f"Received raw login request: {body_str}")
        
        # Try to parse as form data
        content_type = request.headers.get('content-type', '')
        
        username = None
        password = None
        
        if 'application/x-www-form-urlencoded' in content_type:
            form_data = await request.form()
            username = form_data.get('username')
            password = form_data.get('password')
            logger.info(f"Form data parsed: username={username}, password={'*' * len(password) if password else None}")
        elif 'application/json' in content_type:
            json_data = await request.json()
            username = json_data.get('username')
            password = json_data.get('password')
            logger.info(f"JSON data parsed: username={username}, password={'*' * len(password) if password else None}")
        else:
            # Try to parse from raw body
            pairs = body_str.split('&')
            for pair in pairs:
                if '=' in pair:
                    key, value = pair.split('=', 1)
                    if key == 'username':
                        username = value
                    elif key == 'password':
                        password = value
            
            logger.info(f"Raw body parsed: username={username}, password={'*' * len(password) if password else None}")
        
        if not username or not password:
            return JSONResponse(
                status_code=400,
                content={"detail": "Username and password are required"}
            )
        
        # For debugging, just accept any login
        logger.info(f"Login successful for user: {username}")
        
        # Return a simplified token response - this would normally verify credentials
        return {
            "access_token": "debug_token_for_testing_only",
            "token_type": "bearer"
        }
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": f"Login error: {str(e)}"}
        )


@app.post("/api/interviews/start")
async def start_interview(
    employee_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(SessionLocal),
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
                    "created_at": datetime.now().isoformat(),
                },
            )

        employee_id = employee_data.get("employee_id")
        if not employee_id:
            raise APIException(
                message="employee_id is required",
                status_code=status.HTTP_400_BAD_REQUEST,
                error_code="MISSING_EMPLOYEE_ID",
            )

        interview = crud.create_interview(db, employee_id)

        return success_response(
            message="Interview started successfully",
            data={
                "id": interview.id,
                "employee_id": interview.employee_id,
                "status": interview.status,
                "start_date": interview.start_date.isoformat()
                if interview.start_date
                else None,
                "created_at": interview.created_at.isoformat()
                if interview.created_at
                else None,
            },
        )
    except Exception as e:
        logger.error(f"Error starting interview: {str(e)}")
        raise APIException(
            message=f"Error starting interview: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="INTERVIEW_START_ERROR",
        )


@app.post("/api/interviews/{interview_id}/message")
async def process_message(
    interview_id: int,
    message_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(SessionLocal),
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
                        "text": "What did you enjoy most about working here?",
                    },
                    "is_complete": False,
                },
            )

        message = message_data.get("message")
        if not message:
            raise APIException(
                message="message is required",
                status_code=status.HTTP_400_BAD_REQUEST,
                error_code="MISSING_MESSAGE",
            )

        interview = crud.get_interview(db, interview_id)
        if not interview:
            raise APIException(
                message="Interview not found",
                status_code=status.HTTP_404_NOT_FOUND,
                error_code="INTERVIEW_NOT_FOUND",
            )

        # Process the message and get response
        response = await process_interview_message(db, interview, message)

        return success_response(message="Message processed successfully", data=response)
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise APIException(
            message=f"Error processing message: {str(e)}",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_code="MESSAGE_PROCESSING_ERROR",
        )


@app.get("/api/users/me")
async def get_current_user_me(current_user: User = Depends(get_current_active_user)):
    """Fetch current user's profile information."""
    # In a real app, you might want to return more profile details
    # For now, just return what the frontend was trying to use.
    if not current_user:
         raise APIException(
            message="User not authenticated",
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="NOT_AUTHENTICATED",
        )
    return {"name": current_user.full_name or current_user.username, "email": current_user.email, "role": "admin"} # Placeholder role


@app.get("/api/dashboard/statistics")
async def get_dashboard_statistics_data(start_date: str, end_date: str, current_user: User = Depends(get_current_active_user)):
    """Fetch dashboard statistics for a given date range."""
    # Placeholder data - replace with actual data fetching logic
    logger.info(f"Fetching dashboard stats for user {current_user.username} from {start_date} to {end_date}")
    return {
        "summary_stats": {
            "interviews_total": 120,
            "interviews_complete": 95,
            "interviews_incomplete": 25,
            "avg_sentiment": 3.8, # Assuming a 1-5 scale
            "top_categories": [
                {"category": "Management", "count": 30},
                {"category": "Work-Life Balance", "count": 25},
                {"category": "Compensation", "count": 20},
                {"category": "Career Growth", "count": 15},
                {"category": "Company Culture", "count": 5}
            ]
        },
        "department_breakdown": {
            "Engineering": 30,
            "Sales": 25,
            "Marketing": 20,
            "HR": 15,
            "Finance": 15,
            "Product": 15
        },
        "recent_interviews": [
            {
                "employee_name": "Alice Wonderland",
                "department": "Engineering",
                "date": "2025-05-10",
                "status": "completed"
            },
            {
                "employee_name": "Bob The Builder",
                "department": "Product",
                "date": "2025-05-08",
                "status": "completed"
            },
            {
                "employee_name": "Charlie Brown",
                "department": "Sales",
                "date": "2025-05-05",
                "status": "in_progress"
            }
        ]
    }


# Error handlers
@app.exception_handler(APIException)
async def api_exception_handler(request: Request, exc: APIException):
    return JSONResponse(status_code=exc.status_code, content=exc.detail)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {str(exc)}")
    return error_response(
        message="An unexpected error occurred",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code="INTERNAL_SERVER_ERROR",
        details={"error": str(exc)},
    )


if __name__ == "__main__":
    logger.info("Starting ExitBot Direct API...")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
