"""
Database connection and session management with resilience features
"""
import time
import logging
import random
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, exc, text
from sqlalchemy.orm import sessionmaker

# Use absolute import from the project root
from exitbot.app.core.config import settings

# Configure logger
logger = logging.getLogger(__name__)

class DatabaseConnection:
    """Database connection manager with resilience features"""
    
    def __init__(self, db_url: Optional[str] = None, pool_size: int = 5,
                 max_overflow: int = 10, max_retries: int = 3):
        """
        Initialize database connection
        
        Args:
            db_url: Database connection URL (default: from settings)
            pool_size: Connection pool size
            max_overflow: Maximum pool overflow
            max_retries: Maximum connection retry attempts
        """
        self.db_url = db_url or settings.SQLALCHEMY_DATABASE_URI
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.max_retries = max_retries
        self.engine = None
        self.SessionLocal = None
        
        # Initialize connection pool
        self._initialize_connection()
    
    def _initialize_connection(self) -> None:
        """Initialize database connection with retry mechanism"""
        retry_count = 0
        backoff_time = 1
        
        while retry_count <= self.max_retries:
            try:
                # Create engine with connection pooling
                self.engine = create_engine(
                    self.db_url,
                    pool_size=self.pool_size,
                    max_overflow=self.max_overflow,
                    pool_pre_ping=True,  # Check connection vitality before using
                    pool_recycle=3600    # Recycle connections after 1 hour
                )
                
                # Create sessionmaker
                self.SessionLocal = sessionmaker(
                    autocommit=False,
                    autoflush=False,
                    bind=self.engine
                )
                
                # Test connection
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                
                logger.info("Database connection established successfully")
                return
                
            except (exc.OperationalError, exc.DatabaseError) as e:
                retry_count += 1
                
                if retry_count > self.max_retries:
                    logger.error(f"Failed to connect to database after {self.max_retries} attempts: {str(e)}")
                    raise
                
                # Calculate backoff with jitter
                jitter = random.uniform(0, 0.5)
                sleep_time = backoff_time + jitter
                logger.warning(f"Database connection attempt {retry_count}/{self.max_retries} failed. Retrying in {sleep_time:.1f}s")
                
                # Wait before retrying
                time.sleep(sleep_time)
                
                # Exponential backoff
                backoff_time *= 2
    
    @contextmanager
    def get_db_session(self) -> Generator:
        """
        Get database session with error handling
        
        Yields:
            SQLAlchemy session
        """
        if not self.SessionLocal:
            self._initialize_connection()
            
        db = self.SessionLocal()
        try:
            yield db
        except exc.OperationalError as e:
            # Handle connection errors
            logger.error(f"Database operational error: {str(e)}")
            db.rollback()
            raise
        except exc.IntegrityError as e:
            # Handle integrity errors (e.g., unique constraint violations)
            logger.error(f"Database integrity error: {str(e)}")
            db.rollback()
            raise
        except Exception as e:
            # Handle other exceptions
            logger.error(f"Error during database session: {str(e)}")
            db.rollback()
            raise
        finally:
            db.close()

# Create a singleton database connection
db_connection = DatabaseConnection()

def get_db() -> Generator:
    """
    Get database session
    
    Yields:
        SQLAlchemy session
    """
    with db_connection.get_db_session() as db:
        yield db 