from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy.orm import Session

from exitbot.app.core.logging import get_logger
from exitbot.app.db import crud
from exitbot.app.db.models import Interview, Question, Response
from exitbot.app.llm.factory import llm_client
from exitbot.app.llm.prompts import (
    DEFAULT_QUESTIONS,
    get_interview_prompt,
    get_follow_up_prompt,
)

logger = get_logger("services.interview")


class InterviewService:
    """Service for managing interview flows and interactions"""

    @staticmethod
    def start_interview(
        db: Session, employee_id: int, exit_date: Optional[datetime] = None
    ) -> Interview:
        """
        Start a new exit interview

        Args:
            db: Database session
            employee_id: ID of the employee
            exit_date: Date when the employee is leaving

        Returns:
            Interview: Created interview object
        """
        # Create interview
        interview = crud.create_interview(db, employee_id, exit_date)

        # Ensure default questions exist
        InterviewService._ensure_default_questions(db)

        return interview

    @staticmethod
    def _ensure_default_questions(db: Session) -> None:
        """Ensure default questions exist in the database"""
        # Get all questions
        questions = crud.get_all_questions(db)

        # If no questions exist, create defaults
        if not questions:
            logger.info("Creating default interview questions")
            for i, question_text in enumerate(DEFAULT_QUESTIONS):
                crud.create_question(
                    db,
                    {
                        "text": question_text,
                        "order_num": i + 1,
                        "category": "default",
                        "is_active": True,
                    },
                )

    @staticmethod
    def get_current_question(db: Session, interview_id: int) -> Optional[Question]:
        """
        Get the current question for an interview

        Args:
            db: Database session
            interview_id: ID of the interview

        Returns:
            Question: Current question or None if all questions answered
        """
        # Get all active questions
        questions = crud.get_all_questions(db)
        if not questions:
            return None

        # Get all responses for this interview
        responses = crud.get_responses_by_interview(db, interview_id)

        # Group responses by question
        answered_questions = set()
        for response in responses:
            answered_questions.add(response.question_id)

        # Find the first unanswered question
        for question in questions:
            if question.id not in answered_questions:
                return question

        # If we get here, all questions have been answered
        return None

    @staticmethod
    def process_message(
        db: Session, interview_id: int, message: str, question_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Process a message from the employee

        Args:
            db: Database session
            interview_id: ID of the interview
            message: Message from the employee
            question_id: ID of the current question (optional)

        Returns:
            dict: Response with bot message and next question
        """
        # Get the interview
        interview = crud.get_interview(db, interview_id)
        if not interview:
            raise ValueError(f"Interview with ID {interview_id} not found")

        # Get the user
        user = crud.get_user(db, interview.employee_id)
        if not user:
            raise ValueError(f"Employee with ID {interview.employee_id} not found")

        # If no question_id is provided, get the current question
        current_question = None
        if question_id:
            current_question = crud.get_question(db, question_id)
        else:
            current_question = InterviewService.get_current_question(db, interview_id)

        if not current_question:
            # All questions answered
            InterviewService.complete_interview(db, interview_id)
            return {
                "response": "Thank you for completing the exit interview! Your feedback is valuable to us.",
                "current_question": None,
                "is_complete": True,
            }

        # Get previous questions and responses
        question_history = InterviewService._get_question_history(db, interview_id)

        # Generate bot response
        prompt = get_interview_prompt(
            current_question=current_question.text,
            employee_response=message,
            question_history=question_history,
            employee_name=user.full_name,
        )

        response = llm_client.generate_response(prompt)
        bot_response = response.get(
            "response", "I'm sorry, I couldn't process your response."
        )

        # Analyze sentiment
        sentiment = llm_client.analyze_sentiment(message)

        # Save response
        crud.create_response(
            db,
            {
                "interview_id": interview_id,
                "question_id": current_question.id,
                "employee_message": message,
                "bot_response": bot_response,
                "sentiment": sentiment,
            },
        )

        # Check if we need to move to the next question or follow up
        next_question = InterviewService._determine_next_question(
            db, interview_id, current_question, message
        )

        is_complete = next_question is None
        if is_complete:
            InterviewService.complete_interview(db, interview_id)

        return {
            "response": bot_response,
            "current_question": next_question,
            "is_complete": is_complete,
        }

    @staticmethod
    def _get_question_history(db: Session, interview_id: int) -> List[Dict[str, str]]:
        """Get history of questions and responses for context"""
        responses = crud.get_responses_by_interview(db, interview_id)

        history = []
        for response in responses:
            question = crud.get_question(db, response.question_id)
            if question:
                history.append(
                    {
                        "question": question.text,
                        "employee_response": response.employee_message,
                        "bot_response": response.bot_response,
                    }
                )

        return history

    @staticmethod
    def _determine_next_question(
        db: Session,
        interview_id: int,
        current_question: Question,
        employee_response: str,
    ) -> Optional[Question]:
        """
        Determine if we should follow up or move to the next question

        Args:
            db: Database session
            interview_id: ID of the interview
            current_question: Current question
            employee_response: Employee's response

        Returns:
            Question: Next question or None if all questions answered
        """
        # Count responses for this question in this interview
        responses = (
            db.query(Response)
            .filter(
                Response.interview_id == interview_id,
                Response.question_id == current_question.id,
            )
            .count()
        )

        # If we've had fewer than 2 exchanges on this question,
        # check if we need a follow-up
        if responses < 2:
            # Get follow-up prompt
            prompt = get_follow_up_prompt(
                primary_question=current_question.text,
                employee_response=employee_response,
                follow_up_count=responses,
            )

            response = llm_client.generate_response(prompt, temperature=0.3)
            follow_up = response.get("response", "NO_FOLLOWUP").strip()

            # If a follow-up is suggested, stay on the current question
            if follow_up != "NO_FOLLOWUP" and not follow_up.startswith("NO_FOLLOWUP"):
                return current_question

        # Move to the next question
        questions = crud.get_all_questions(db)
        for i, question in enumerate(questions):
            if question.id == current_question.id and i + 1 < len(questions):
                return questions[i + 1]

        # No more questions
        return None

    @staticmethod
    def complete_interview(db: Session, interview_id: int) -> Interview:
        """
        Mark an interview as complete

        Args:
            db: Database session
            interview_id: ID of the interview

        Returns:
            Interview: Updated interview object
        """
        return crud.update_interview_status(db, interview_id, "completed")

def process_interview_message(db, interview_id, message, question_id=None):
    """
    Wrapper for InterviewService.process_message to maintain backward compatibility.
    """
    return InterviewService.process_message(db, interview_id, message, question_id)
