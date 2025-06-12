"""
Database query optimization utilities and configuration

This module contains functions and configurations for optimizing database 
performance, including index creation and query optimization.
"""
from sqlalchemy.sql import text
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy.sql import select, func
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import Executable
from sqlalchemy import Index

from exitbot.database.models import User, ExitInterview, Question, Answer
from exitbot.database.database import engine

logger = logging.getLogger(__name__)


class CreateIndex(Executable):
    """CreateIndex executable for conditional index creation"""

    def __init__(self, name, table, *expressions, **kw):
        self.name = name
        self.table = table
        self.expressions = expressions
        self.kw = kw


@compiles(CreateIndex)
def visit_create_index(create, compiler, **kw):
    """SQL compilation for conditional index creation"""
    index = Index(create.name, *create.expressions, **create.kw)
    return "CREATE INDEX IF NOT EXISTS %s ON %s %s" % (
        index.name,
        create.table,
        compiler.sql_compiler.process(index, include_table=False, include_schema=False),
    )


def setup_indexes():
    """
    Create indexes to optimize query performance

    This function creates indexes that are most beneficial for frequently used queries.
    """
    with engine.connect() as conn:
        try:
            # Interview status index for filtering by status
            conn.execute(
                CreateIndex(
                    "ix_exit_interviews_status", "exit_interviews", ExitInterview.status
                )
            )
            logger.info("Created index on exit_interviews.status")

            # Exit interview date range index for reporting
            conn.execute(
                CreateIndex(
                    "ix_exit_interviews_created_at",
                    "exit_interviews",
                    ExitInterview.created_at,
                )
            )
            logger.info("Created index on exit_interviews.created_at")

            # User email index for authentication
            conn.execute(CreateIndex("ix_users_email", "users", User.email))
            logger.info("Created index on users.email")

            # Department index for reporting queries
            conn.execute(CreateIndex("ix_users_department", "users", User.department))
            logger.info("Created index on users.department")

            # Question category for filtering
            conn.execute(
                CreateIndex("ix_questions_category", "questions", Question.category)
            )
            logger.info("Created index on questions.category")

            # Composite index for answer lookups
            conn.execute(
                CreateIndex(
                    "ix_answers_interview_question",
                    "answers",
                    Answer.exit_interview_id,
                    Answer.question_id,
                )
            )
            logger.info("Created index on answers.(exit_interview_id, question_id)")

            # Answers created_at for timeline queries
            conn.execute(
                CreateIndex("ix_answers_created_at", "answers", Answer.created_at)
            )
            logger.info("Created index on answers.created_at")

            conn.commit()
            logger.info("Successfully created all indexes")

        except Exception as e:
            logger.error(f"Error creating indexes: {str(e)}")
            conn.rollback()
            raise


def optimize_department_query(db: Session):
    """
    Optimize the department breakdown query by using a subquery approach

    This optimization reduces the amount of data processed by first calculating
    interview counts separately from sentiment scores.

    Args:
        db: Database session

    Returns:
        The compiled SQL statement for manual execution
    """
    # First, create a subquery for interview counts
    interview_counts = (
        select([User.department, func.count(ExitInterview.id).label("interview_count")])
        .select_from(User.__table__.join(ExitInterview.__table__))
        .group_by(User.department)
        .alias("interview_counts")
    )

    # Then, create a subquery for sentiment scores
    sentiment_scores = (
        select([User.department, func.avg(Answer.sentiment).label("avg_sentiment")])
        .select_from(
            User.__table__.join(ExitInterview.__table__).join(Answer.__table__)
        )
        .group_by(User.department)
        .alias("sentiment_scores")
    )

    # Finally, join these subqueries
    stmt = select(
        [
            interview_counts.c.department,
            interview_counts.c.interview_count,
            sentiment_scores.c.avg_sentiment,
        ]
    ).select_from(
        interview_counts.outerjoin(
            sentiment_scores,
            interview_counts.c.department == sentiment_scores.c.department,
        )
    )

    return str(stmt.compile(compile_kwargs={"literal_binds": True}))


def optimize_exit_reason_query(db: Session):
    """
    Optimize the exit reason query by using window functions

    This optimization counts exit reasons more efficiently.

    Args:
        db: Database session

    Returns:
        The compiled SQL statement for manual execution
    """
    stmt = text(
        """
    WITH exit_reasons AS (
        SELECT 
            a.answer_text,
            CASE 
                WHEN a.answer_text ILIKE '%salary%' OR a.answer_text ILIKE '%compensation%' OR a.answer_text ILIKE '%pay%'
                THEN 'Compensation'
                WHEN a.answer_text ILIKE '%opportunity%' OR a.answer_text ILIKE '%growth%' OR a.answer_text ILIKE '%career%'
                THEN 'Career Growth'
                WHEN a.answer_text ILIKE '%balance%' OR a.answer_text ILIKE '%hours%' OR a.answer_text ILIKE '%workload%'
                THEN 'Work-Life Balance'
                WHEN a.answer_text ILIKE '%manager%' OR a.answer_text ILIKE '%leadership%' OR a.answer_text ILIKE '%boss%'
                THEN 'Management Issues'
                WHEN a.answer_text ILIKE '%culture%' OR a.answer_text ILIKE '%environment%' OR a.answer_text ILIKE '%toxic%'
                THEN 'Company Culture'
                ELSE 'Other'
            END AS reason_category
        FROM 
            answers a
        JOIN 
            questions q ON a.question_id = q.id
        JOIN 
            exit_interviews e ON a.exit_interview_id = e.id
        WHERE 
            q.text ILIKE '%why%leaving%' OR q.text ILIKE '%reason%departure%'
    )
    
    SELECT 
        reason_category,
        COUNT(*) as count
    FROM 
        exit_reasons
    GROUP BY 
        reason_category
    ORDER BY 
        count DESC
    LIMIT 5
    """
    )

    return str(stmt)


class QueryCache:
    """Simple query result cache"""

    _cache = {}

    @staticmethod
    def get(key: str) -> Optional[Any]:
        """Get a cached query result"""
        return QueryCache._cache.get(key)

    @staticmethod
    def set(key: str, value: Any) -> None:
        """Set a cached query result"""
        QueryCache._cache[key] = value

    @staticmethod
    def invalidate(prefix: Optional[str] = None) -> None:
        """Invalidate cache entries"""
        if prefix:
            # Remove entries starting with prefix
            keys_to_remove = [
                k for k in QueryCache._cache.keys() if k.startswith(prefix)
            ]
            for key in keys_to_remove:
                del QueryCache._cache[key]
        else:
            # Clear entire cache
            QueryCache._cache.clear()


def cached_query(func):
    """
    Decorator for caching query results

    Args:
        func: The function to decorate

    Returns:
        Decorated function with caching
    """

    def wrapper(*args, **kwargs):
        # Generate cache key from function name and arguments
        key_parts = [func.__name__]
        key_parts.extend(str(arg) for arg in args if not isinstance(arg, Session))
        key_parts.extend(f"{k}:{v}" for k, v in kwargs.items())
        key = ":".join(key_parts)

        # Check cache
        cached_result = QueryCache.get(key)
        if cached_result is not None:
            logger.debug(f"Cache hit for query {key}")
            return cached_result

        # Execute query
        result = func(*args, **kwargs)

        # Cache result
        QueryCache.set(key, result)
        logger.debug(f"Cached query result for {key}")

        return result

    return wrapper


def explain_analyze_query(db: Session, sql: str) -> List[Dict[str, Any]]:
    """
    Run EXPLAIN ANALYZE on a given SQL query to help with optimization

    Args:
        db: Database session
        sql: SQL statement to analyze

    Returns:
        Analysis of the query execution plan
    """
    try:
        result = db.execute(text(f"EXPLAIN ANALYZE {sql}"))
        rows = result.fetchall()
        return [{"plan_line": row[0]} for row in rows]
    except Exception as e:
        logger.error(f"Error analyzing query: {str(e)}")
        return [{"error": str(e)}]
