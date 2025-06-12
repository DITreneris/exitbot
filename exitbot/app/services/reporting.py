from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from sqlalchemy import func

from exitbot.app.core.logging import get_logger
from exitbot.app.db import crud
from exitbot.app.db.models import Interview, Response, User, Question
from exitbot.app.llm.factory import llm_client
from exitbot.app.llm.prompts import get_summary_prompt
from exitbot.app.services.caching import ttl_cache

logger = get_logger("services.reporting")


class ReportingService:
    """Service for generating reports from exit interviews"""

    @staticmethod
    @ttl_cache(ttl=600)  # 10 minutes cache
    def get_summary_stats(
        db: Session, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> Dict[str, Any]:
        """
        Get summary statistics for exit interviews

        Args:
            db: Database session
            start_date: Start date for filtering
            end_date: End date for filtering

        Returns:
            dict: Summary statistics
        """
        logger.info(f"Generating summary stats for {start_date} to {end_date}")

        # Set default date range if not provided (last 30 days)
        if not end_date:
            end_date = datetime.utcnow().date()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # Convert to datetime for comparison
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

        # Query interviews in date range
        query = db.query(Interview).filter(
            Interview.created_at >= start_datetime, Interview.created_at <= end_datetime
        )

        total_interviews = query.count()
        completed_interviews = query.filter(Interview.status == "completed").count()
        in_progress_interviews = query.filter(Interview.status == "in_progress").count()

        # Calculate average sentiment
        avg_sentiment = (
            db.query(func.avg(Response.sentiment))
            .join(Interview, Response.interview_id == Interview.id)
            .filter(
                Interview.created_at >= start_datetime,
                Interview.created_at <= end_datetime,
            )
            .scalar()
        )

        if avg_sentiment is not None:
            avg_sentiment = float(avg_sentiment)

        # Get top exit reasons
        top_reasons = ReportingService._extract_exit_reasons(
            db, start_datetime, end_datetime
        )

        return {
            "total_interviews": total_interviews,
            "completed_interviews": completed_interviews,
            "in_progress_interviews": in_progress_interviews,
            "average_sentiment": avg_sentiment,
            "top_exit_reasons": top_reasons,
        }

    @staticmethod
    def _extract_exit_reasons(
        db: Session, start_date: datetime, end_date: datetime, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Extract top reasons for leaving from exit interviews"""
        # Get first question responses (usually about why leaving)
        first_question = db.query(Question).order_by(Question.order_num).first()
        if not first_question:
            return []

        # Get responses to the first question
        responses = (
            db.query(Response)
            .join(Interview, Response.interview_id == Interview.id)
            .filter(
                Response.question_id == first_question.id,
                Interview.created_at >= start_date,
                Interview.created_at <= end_date,
                Interview.status == "completed",
            )
            .all()
        )

        if not responses:
            return []

        # Use LLM to categorize reasons (in a real application, this would be more sophisticated)
        reasons = {}
        for response in responses:
            # Very basic categorization - in a real app, use LLM clustering
            message = response.employee_message.lower()

            if "salary" in message or "compensation" in message or "pay" in message:
                reasons["Compensation"] = reasons.get("Compensation", 0) + 1
            elif "opportunity" in message or "growth" in message or "career" in message:
                reasons["Career Growth"] = reasons.get("Career Growth", 0) + 1
            elif "balance" in message or "hours" in message or "workload" in message:
                reasons["Work-Life Balance"] = reasons.get("Work-Life Balance", 0) + 1
            elif "manager" in message or "leadership" in message or "boss" in message:
                reasons["Management Issues"] = reasons.get("Management Issues", 0) + 1
            elif "culture" in message or "environment" in message or "toxic" in message:
                reasons["Company Culture"] = reasons.get("Company Culture", 0) + 1
            else:
                reasons["Other"] = reasons.get("Other", 0) + 1

        # Sort and format results
        sorted_reasons = sorted(reasons.items(), key=lambda x: x[1], reverse=True)
        return [{"reason": r[0], "count": r[1]} for r in sorted_reasons[:limit]]

    @staticmethod
    @ttl_cache(ttl=900)  # 15 minutes cache
    def get_department_breakdown(
        db: Session, start_date: Optional[date] = None, end_date: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """
        Get breakdown of exit interviews by department

        Args:
            db: Database session
            start_date: Start date for filtering
            end_date: End date for filtering

        Returns:
            list: Department statistics
        """
        logger.info(f"Generating department breakdown for {start_date} to {end_date}")

        # Set default date range if not provided (last 90 days)
        if not end_date:
            end_date = datetime.utcnow().date()
        if not start_date:
            start_date = end_date - timedelta(days=90)

        # Convert to datetime for comparison
        start_datetime = datetime.combine(start_date, datetime.min.time())
        end_datetime = datetime.combine(end_date, datetime.max.time())

        # Get interviews by department
        departments = (
            db.query(
                User.department,
                func.count(Interview.id).label("interview_count"),
                func.avg(Response.sentiment).label("sentiment_score"),
            )
            .join(Interview, User.id == Interview.employee_id)
            .join(Response, Interview.id == Response.interview_id)
            .filter(
                Interview.created_at >= start_datetime,
                Interview.created_at <= end_datetime,
            )
            .group_by(User.department)
            .all()
        )

        # Format results
        return [
            {
                "department": dept or "Unknown",
                "interview_count": count,
                "sentiment_score": float(score) if score is not None else None,
            }
            for dept, count, score in departments
        ]

    @staticmethod
    @ttl_cache(ttl=1800)  # 30 minutes cache for summaries
    def generate_interview_summary(db: Session, interview_id: int) -> str:
        """
        Generate a summary of an exit interview

        Args:
            db: Database session
            interview_id: ID of the interview

        Returns:
            str: Summary of the interview
        """
        logger.info(f"Generating summary for interview ID {interview_id}")

        # Get the interview
        interview = crud.get_interview(db, interview_id)
        if not interview:
            raise ValueError(f"Interview with ID {interview_id} not found")

        # Get the user
        user = crud.get_user(db, interview.employee_id)
        if not user:
            raise ValueError(f"Employee with ID {interview.employee_id} not found")

        # Get responses
        responses = crud.get_responses_by_interview(db, interview_id)
        if not responses:
            return "No responses found for this interview."

        # Format responses for the prompt
        formatted_responses = []
        for response in responses:
            question = crud.get_question(db, response.question_id)
            if question:
                formatted_responses.append(
                    {
                        "question": question.text,
                        "employee_response": response.employee_message,
                    }
                )

        # Generate summary with LLM
        prompt = get_summary_prompt(formatted_responses)
        response = llm_client.generate_response(prompt)

        return response.get("response", "Unable to generate summary.")

    @staticmethod
    def invalidate_report_caches():
        """
        Invalidate any cached reports when new data is available
        This is a placeholder method for now
        """
        logger.info("Invalidating report caches")
