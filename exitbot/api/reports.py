from datetime import datetime, date
from typing import List, Optional, Dict, Any, Union
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from exitbot.database.crud import get_all_interviews, get_interview, get_interview_by_id
from exitbot.database.database import get_db
from exitbot.database.models import User, Interview, Response
from exitbot.api.auth import get_current_user
from exitbot.ai.sentiment import analyze_sentiment

router = APIRouter(prefix="/api/reports", tags=["reports"])

@router.get("/summary")
async def get_summary_stats(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get summary statistics for exit interviews"""
    if not current_user.is_hr and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access reports")
    
    # Get all interviews within date range
    interviews = get_all_interviews(
        db, 
        start_date=start_date, 
        end_date=end_date,
        skip=0,
        limit=1000  # Set a high limit to get all interviews
    )
    
    # Calculate statistics
    total_interviews = len(interviews)
    completed_interviews = sum(1 for interview in interviews if interview.status == "completed")
    in_progress_interviews = total_interviews - completed_interviews
    
    # Calculate average sentiment
    sentiments = []
    for interview in interviews:
        for response in interview.responses:
            if response.sentiment is not None:
                sentiments.append(float(response.sentiment))
    
    average_sentiment = sum(sentiments) / len(sentiments) if sentiments else None
    
    # Calculate top exit reasons
    exit_reasons = {}
    for interview in interviews:
        # Look for the response that contains exit reason
        for response in interview.responses:
            # Check if this is the exit reason question
            if "reason" in response.question_text.lower() and "leaving" in response.question_text.lower():
                # Simple logic to extract reason - in a real system this might use NLP
                reason = response.employee_message
                if len(reason) > 50:
                    reason = reason[:50] + "..."
                
                if reason in exit_reasons:
                    exit_reasons[reason] += 1
                else:
                    exit_reasons[reason] = 1
                break
    
    # Sort reasons by frequency
    top_exit_reasons = [{"reason": reason, "count": count} for reason, count in exit_reasons.items()]
    top_exit_reasons.sort(key=lambda x: x["count"], reverse=True)
    
    return {
        "total_interviews": total_interviews,
        "completed_interviews": completed_interviews,
        "in_progress_interviews": in_progress_interviews,
        "average_sentiment": average_sentiment,
        "top_exit_reasons": top_exit_reasons[:5]  # Return top 5 reasons
    }

@router.get("/by-department")
async def get_department_breakdown(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get department breakdown for exit interviews"""
    if not current_user.is_hr and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access reports")
    
    # Get all interviews within date range
    interviews = get_all_interviews(
        db, 
        start_date=start_date, 
        end_date=end_date,
        skip=0,
        limit=1000
    )
    
    # Group by department
    departments = {}
    for interview in interviews:
        department = interview.department if interview.department else "Unknown"
        
        if department not in departments:
            departments[department] = {
                "interview_count": 0,
                "sentiments": [],
            }
        
        departments[department]["interview_count"] += 1
        
        # Calculate sentiment for this interview
        for response in interview.responses:
            if response.sentiment is not None:
                departments[department]["sentiments"].append(float(response.sentiment))
    
    # Calculate average sentiment for each department
    result = {"departments": []}
    for dept, data in departments.items():
        avg_sentiment = sum(data["sentiments"]) / len(data["sentiments"]) if data["sentiments"] else None
        
        result["departments"].append({
            "department": dept,
            "interview_count": data["interview_count"],
            "sentiment_score": avg_sentiment
        })
    
    # Sort by interview count (descending)
    result["departments"].sort(key=lambda x: x["interview_count"], reverse=True)
    
    return result

@router.get("/interview/{interview_id}/summary")
async def get_interview_summary(
    interview_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate a summary for a specific interview"""
    if not current_user.is_hr and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access this resource")
    
    # Get the interview
    interview = get_interview_by_id(db, interview_id)
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Generate summary
    # For a simple version, we'll just collect key information
    # In a real system, this could use an LLM to generate a more coherent summary
    summary = f"## Exit Interview Summary for Employee #{interview.employee_id}\n\n"
    
    # Basic information
    summary += f"**Interview Date:** {interview.created_at.strftime('%Y-%m-%d')}\n"
    summary += f"**Department:** {interview.department or 'Not specified'}\n"
    summary += f"**Status:** {interview.status.capitalize()}\n\n"
    
    # Sentiment analysis
    sentiments = [float(r.sentiment) for r in interview.responses if r.sentiment is not None]
    avg_sentiment = sum(sentiments) / len(sentiments) if sentiments else None
    
    if avg_sentiment is not None:
        sentiment_desc = "Positive" if avg_sentiment > 0.3 else "Neutral" if avg_sentiment > -0.3 else "Negative"
        summary += f"**Overall Sentiment:** {sentiment_desc} ({avg_sentiment:.2f})\n\n"
    
    # Key insights
    summary += "### Key Insights\n\n"
    
    # Exit reason
    exit_reason_response = None
    for response in interview.responses:
        if "reason" in response.question_text.lower() and "leaving" in response.question_text.lower():
            exit_reason_response = response
            break
    
    if exit_reason_response:
        summary += f"**Reason for Leaving:** {exit_reason_response.employee_message}\n\n"
    
    # Positive aspects
    positive_responses = [r for r in interview.responses if r.sentiment is not None and float(r.sentiment) > 0.5]
    if positive_responses:
        summary += "**Positive Aspects:**\n"
        for response in positive_responses[:3]:  # Top 3 positive responses
            summary += f"- *{response.question_text}*: {response.employee_message[:100]}...\n"
        summary += "\n"
    
    # Areas of concern
    negative_responses = [r for r in interview.responses if r.sentiment is not None and float(r.sentiment) < -0.3]
    if negative_responses:
        summary += "**Areas of Concern:**\n"
        for response in negative_responses[:3]:  # Top 3 negative responses
            summary += f"- *{response.question_text}*: {response.employee_message[:100]}...\n"
        summary += "\n"
    
    # Recommendations
    summary += "### Recommendations\n\n"
    if negative_responses:
        summary += "- Review concerns raised about " + ", ".join([r.question_text.split("?")[0] for r in negative_responses[:2]]) + "\n"
    
    summary += "- Follow up with employee regarding their transition\n"
    
    if avg_sentiment is not None and avg_sentiment < -0.3:
        summary += "- Consider addressing organizational issues highlighted in the interview\n"
    
    return summary

@router.get("/export")
async def export_interview_data(
    format: str = Query("json", description="Export format (json or csv)"),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    department: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export interview data in JSON or CSV format"""
    if not current_user.is_hr and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized to access reports")
    
    # Validate format
    if format not in ["json", "csv"]:
        raise HTTPException(status_code=400, detail="Format must be 'json' or 'csv'")
    
    # Get all interviews within parameters
    interviews = get_all_interviews(
        db, 
        start_date=start_date, 
        end_date=end_date,
        department=department,
        skip=0,
        limit=1000
    )
    
    # Prepare data for export
    export_data = []
    for interview in interviews:
        interview_data = {
            "id": interview.id,
            "employee_id": interview.employee_id,
            "department": interview.department,
            "status": interview.status,
            "created_at": interview.created_at.isoformat(),
            "responses": []
        }
        
        # Add responses
        for response in interview.responses:
            response_data = {
                "question": response.question_text,
                "employee_message": response.employee_message,
                "bot_response": response.bot_response,
                "sentiment": float(response.sentiment) if response.sentiment is not None else None
            }
            interview_data["responses"].append(response_data)
        
        export_data.append(interview_data)
    
    return export_data 