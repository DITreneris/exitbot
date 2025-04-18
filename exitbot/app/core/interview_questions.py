# exitbot/app/core/interview_questions.py

PREDEFINED_QUESTIONS = [
    {"id": 1, "text": "What primarily motivated your decision to leave our organization?"},
    {"id": 2, "text": "Was there a specific event or circumstance that triggered your resignation?"},
    {"id": 3, "text": "What aspects of your role did you find most fulfilling?"},
    {"id": 4, "text": "What challenges or frustrations did you encounter in your position?"},
    {"id": 5, "text": "How would you assess your relationship with your direct manager?"},
    {"id": 6, "text": "Did you receive adequate feedback and support for your professional development?"},
    {"id": 7, "text": "How effectively did leadership communicate expectations and company direction?"},
    {"id": 8, "text": "Did you feel your skills and talents were fully utilized in your role?"},
    {"id": 9, "text": "How would you describe the team dynamics and collaboration in your department?"},
    {"id": 10, "text": "Did you feel valued and included as a team member?"},
    {"id": 11, "text": "Were there sufficient opportunities for career advancement or professional growth?"},
    {"id": 12, "text": "How well did the organization recognize and reward your contributions?"},
    {"id": 13, "text": "Did the company culture align with your values and work style?"},
    {"id": 14, "text": "How would you rate your work-life balance during your employment?"},
    {"id": 15, "text": "What improvements would you suggest regarding company processes or structure?"},
    {"id": 16, "text": "Were you provided with adequate resources and tools to perform effectively?"},
    {"id": 17, "text": "What specific changes might have convinced you to stay with the company?"},
    {"id": 18, "text": "Would you consider returning to the organization in the future? Why or why not?"},
    {"id": 19, "text": "Would you recommend our company to others seeking employment? Why or why not?"},
    {"id": 20, "text": "What advice would you offer to help us improve the employee experience?"}
]

# Helper function to get a question by its order (1-based index)
def get_question_by_order(order_num: int):
    """Retrieves a predefined question by its 1-based order number."""
    if 1 <= order_num <= len(PREDEFINED_QUESTIONS):
        # Assuming the list is ordered and id matches order_num for simplicity
        return PREDEFINED_QUESTIONS[order_num - 1]
    return None 