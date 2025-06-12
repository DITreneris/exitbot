# exitbot/app/core/interview_questions.py
from typing import Dict, List, Optional

# Rename from PREDEFINED_QUESTIONS to INTERVIEW_QUESTIONS for consistency with the plan
INTERVIEW_QUESTIONS = [
    {
        "id": 1,
        "text": "What primarily motivated your decision to leave our organization?",
        "category": "Reasons",
    },
    {
        "id": 2,
        "text": "Was there a specific event or circumstance that triggered your resignation?",
        "category": "Reasons",
    },
    {
        "id": 3,
        "text": "What aspects of your role did you find most fulfilling?",
        "category": "Experience",
    },
    {
        "id": 4,
        "text": "What challenges or frustrations did you encounter in your position?",
        "category": "Experience",
    },
    {
        "id": 5,
        "text": "How would you assess your relationship with your direct manager?",
        "category": "Management",
    },
    {
        "id": 6,
        "text": "Did you receive adequate feedback and support for your professional development?",
        "category": "Development",
    },
    {
        "id": 7,
        "text": "How effectively did leadership communicate expectations and company direction?",
        "category": "Leadership",
    },
    {
        "id": 8,
        "text": "Did you feel your skills and talents were fully utilized in your role?",
        "category": "Engagement",
    },
    {
        "id": 9,
        "text": "How would you describe the team dynamics and collaboration in your department?",
        "category": "Culture",
    },
    {
        "id": 10,
        "text": "Did you feel valued and included as a team member?",
        "category": "Culture",
    },
    {
        "id": 11,
        "text": "Were there sufficient opportunities for career advancement or professional growth?",
        "category": "Development",
    },
    {
        "id": 12,
        "text": "How well did the organization recognize and reward your contributions?",
        "category": "Recognition",
    },
    {
        "id": 13,
        "text": "Did the company culture align with your values and work style?",
        "category": "Culture",
    },
    {
        "id": 14,
        "text": "How would you rate your work-life balance during your employment?",
        "category": "Wellbeing",
    },
    {
        "id": 15,
        "text": "What improvements would you suggest regarding company processes or structure?",
        "category": "Improvement",
    },
    {
        "id": 16,
        "text": "Were you provided with adequate resources and tools to perform effectively?",
        "category": "Resources",
    },
    {
        "id": 17,
        "text": "What specific changes might have convinced you to stay with the company?",
        "category": "Retention",
    },
    {
        "id": 18,
        "text": "Would you consider returning to the organization in the future? Why or why not?",
        "category": "Future",
    },
    {
        "id": 19,
        "text": "Would you recommend our company to others seeking employment? Why or why not?",
        "category": "Recommendation",
    },
    {
        "id": 20,
        "text": "What advice would you offer to help us improve the employee experience?",
        "category": "Improvement",
    },
]


def get_question_by_order(order: int) -> Optional[Dict]:
    """
    Get a question by its order in the sequence.

    Args:
        order: The position of the question (1-based index)

    Returns:
        The question dict or None if not found
    """
    if order < 1 or order > len(INTERVIEW_QUESTIONS):
        return None

    return INTERVIEW_QUESTIONS[order - 1]


def get_question_by_id(question_id: int) -> Optional[Dict]:
    """
    Get a question by its ID.

    Args:
        question_id: The unique ID of the question

    Returns:
        The question dict or None if not found
    """
    for question in INTERVIEW_QUESTIONS:
        if question["id"] == question_id:
            return question
    return None


def get_question_count() -> int:
    """
    Get the total number of questions.

    Returns:
        The number of questions in the predefined list
    """
    return len(INTERVIEW_QUESTIONS)


def get_all_questions() -> List[Dict]:
    """
    Get all predefined questions.

    Returns:
        The list of all questions
    """
    return INTERVIEW_QUESTIONS
