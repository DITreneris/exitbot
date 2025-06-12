from sqlalchemy.orm import Session

from exitbot.database.database import SessionLocal, engine
from exitbot.database.models import User, UserRole, Question
from exitbot.app.db.base import Base


def init_db():
    # Create tables
    Base.metadata.create_all(bind=engine)


def create_initial_data(db: Session):
    # Check if we already have data
    if db.query(User).first():
        return

    # Create admin user
    admin = User(
        email="admin@example.com",
        name="Admin User",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password"
        role=UserRole.ADMIN,
    )
    db.add(admin)

    # Create HR user
    hr = User(
        email="hr@example.com",
        name="HR Manager",
        hashed_password="$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # "password"
        role=UserRole.HR,
    )
    db.add(hr)

    # Create some default questions
    questions = [
        Question(
            text="How would you rate your overall experience working here?",
            category="General",
            question_type="rating",
        ),
        Question(
            text="What were the primary reasons for your decision to leave?",
            category="Departure Reasons",
            question_type="multiple_choice",
        ),
        Question(
            text="What aspects of your job did you enjoy the most?",
            category="Job Satisfaction",
            question_type="text",
        ),
        Question(
            text="What aspects of your job did you enjoy the least?",
            category="Job Satisfaction",
            question_type="text",
        ),
        Question(
            text="Do you feel you received adequate feedback and recognition?",
            category="Management",
            question_type="yes_no",
        ),
        Question(
            text="Would you recommend this company to others as a good place to work?",
            category="General",
            question_type="yes_no",
        ),
        Question(
            text="Any additional comments or suggestions for improvement?",
            category="Feedback",
            question_type="text",
        ),
    ]

    for question in questions:
        db.add(question)

    db.commit()


if __name__ == "__main__":
    init_db()
    db = SessionLocal()
    create_initial_data(db)
    db.close()
    print("Database initialized with initial data.")
