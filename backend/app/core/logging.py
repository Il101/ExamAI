"""
Structured logging configuration for production.

Provides JSON-formatted logging for better parsing in log aggregation systems
like CloudWatch, Datadog, or ELK stack.
"""
import logging
import sys
from typing import Any, Dict
from datetime import datetime

from pythonjsonlogger import jsonlogger

from app.core.config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with additional fields."""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """
        Add custom fields to log record.
        
        Args:
            log_record: Dict to be logged as JSON
            record: Standard Python LogRecord
            message_dict: Dict from log message
        """
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp in ISO format
        log_record['timestamp'] = datetime.utcnow().isoformat()
        
        # Add environment
        log_record['environment'] = settings.ENVIRONMENT
        
        # Add service name
        log_record['service'] = 'examai-backend'
        
        # Add level name
        log_record['level'] = record.levelname
        
        # Add logger name
        log_record['logger'] = record.name
        
        # Add file location
        log_record['file'] = f"{record.filename}:{record.lineno}"
        
        # Add function name
        if record.funcName:
            log_record['function'] = record.funcName


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    """
    Configure structured JSON logging for production.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Configured root logger
    """
    # Get root logger
    logger = logging.getLogger()
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Set log level
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    
    # Use JSON formatter in production, simple formatter in development
    if settings.ENVIRONMENT == "production":
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        # Simple format for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Configure third-party loggers
    logging.getLogger('uvicorn').setLevel(logging.INFO)
    logging.getLogger('uvicorn.access').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('celery').setLevel(logging.INFO)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the specified name.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Convenience functions for structured logging

def log_info(logger: logging.Logger, message: str, **kwargs) -> None:
    """Log info message with extra fields."""
    logger.info(message, extra=kwargs)


def log_warning(logger: logging.Logger, message: str, **kwargs) -> None:
    """Log warning message with extra fields."""
    logger.warning(message, extra=kwargs)


def log_error(logger: logging.Logger, message: str, error: Exception | None = None, **kwargs) -> None:
    """Log error message with exception and extra fields."""
    if error:
        kwargs['error_type'] = type(error).__name__
        kwargs['error_message'] = str(error)
    logger.error(message, extra=kwargs, exc_info=error is not None)


def log_debug(logger: logging.Logger, message: str, **kwargs) -> None:
    """Log debug message with extra fields."""
    logger.debug(message, extra=kwargs)


# Example usage:
# from app.core.logging import get_logger, log_info
# logger = get_logger(__name__)
# log_info(logger, "User logged in", user_id="123", email="user@example.com")
