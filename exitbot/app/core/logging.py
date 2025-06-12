"""
Enhanced logging configuration for ExitBot
"""
import logging
import logging.handlers
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from exitbot.app.core.config import settings

# Define log levels
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}

# Define log format
LOG_FORMAT = (
    "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
)
SIMPLE_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"


class ContextFilter(logging.Filter):
    """Add context information to log records"""

    def __init__(self, app_name: str = "exitbot"):
        super().__init__()
        self.app_name = app_name
        self.start_time = time.time()

    def filter(self, record):
        # Add application name
        record.app_name = self.app_name

        # Add request_id if available
        if not hasattr(record, "request_id"):
            record.request_id = "unknown"

        # Add uptime information
        record.uptime = time.time() - self.start_time

        # Add environment information (default to development if not specified)
        record.environment = getattr(settings, "ENVIRONMENT", "development")

        return True


def setup_logging(
    log_level: str = None,
    log_to_file: bool = True,
    log_dir: Optional[str] = None,
    app_name: str = "exitbot",
) -> Dict[str, logging.Logger]:
    """
    Setup enhanced logging for application

    Args:
        log_level: Log level (default: from settings)
        log_to_file: Whether to log to file
        log_dir: Directory for log files (default: logs)
        app_name: Application name for context

    Returns:
        Dict of configured loggers
    """
    # Determine log level
    log_level = log_level or settings.LOG_LEVEL
    level = LOG_LEVELS.get(log_level.lower(), logging.INFO)

    # Create logs directory if it doesn't exist
    log_dir = log_dir or "logs"
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT)
    simple_formatter = logging.Formatter(SIMPLE_FORMAT)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(simple_formatter)
    root_logger.addHandler(console_handler)

    # Create context filter
    context_filter = ContextFilter(app_name)

    # Create file handlers if enabled
    if log_to_file:
        # Create timestamped log file
        timestamp = datetime.now().strftime("%Y%m%d")
        log_file = log_path / f"{app_name}_{timestamp}.log"

        # Create general log file handler
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=10_485_760,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(context_filter)
        root_logger.addHandler(file_handler)

        # Create error log file handler (errors only)
        error_log_file = log_path / f"{app_name}_{timestamp}_errors.log"
        error_file_handler = logging.handlers.RotatingFileHandler(
            filename=error_log_file,
            maxBytes=10_485_760,  # 10 MB
            backupCount=5,
            encoding="utf-8",
        )
        error_file_handler.setLevel(logging.ERROR)
        error_file_handler.setFormatter(formatter)
        error_file_handler.addFilter(context_filter)
        root_logger.addHandler(error_file_handler)

    # Configure module-specific loggers
    loggers = {
        "app": logging.getLogger("app"),
        "db": logging.getLogger("app.db"),
        "api": logging.getLogger("app.api"),
        "llm": logging.getLogger("app.llm"),
        "core": logging.getLogger("app.core"),
    }

    # Apply context filter to all loggers
    for logger in loggers.values():
        logger.addFilter(context_filter)

    # Log startup information
    root_logger.info(f"Logging initialized (level: {log_level.upper()})")
    root_logger.info(f"Environment: {settings.ENVIRONMENT}")

    return loggers


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Get a configured logger

    Args:
        name: Logger name
        level: Optional logging level

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    if level is not None:
        logger.setLevel(level)

    # Only configure handlers if they don't already exist
    if not logger.handlers:
        # Create a console handler
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger
