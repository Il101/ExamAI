"""
Monitoring and error tracking with Sentry.

This module initializes Sentry SDK for error tracking and performance monitoring
in production environment.
"""

import logging
from typing import Optional, Dict, Any, Literal

import sentry_sdk
from sentry_sdk.types import Event, Hint
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.redis import RedisIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from app.core.config import settings

logger = logging.getLogger(__name__)


def filter_sensitive_data(event: Event, hint: Hint) -> Optional[Event]:
    """
    Remove sensitive data before sending to Sentry.

    Args:
        event: Sentry event dict
        hint: Additional context

    Returns:
        Filtered event or None to drop event
    """
    # Filter sensitive fields from request data
    if "request" in event:
        if "data" in event["request"]:
            data = event["request"]["data"]
            if isinstance(data, dict):
                sensitive_fields = [
                    "password",
                    "token",
                    "api_key",
                    "secret",
                    "authorization",
                ]
                for key in sensitive_fields:
                    if key in data:
                        data[key] = "[Filtered]"

        # Filter headers
        if "headers" in event["request"]:
            headers = event["request"]["headers"]
            if isinstance(headers, dict):
                sensitive_headers = ["Authorization", "X-API-Key", "Cookie"]
                for header in sensitive_headers:
                    if header in headers:
                        headers[header] = "[Filtered]"

    # Filter sensitive environment variables
    if "contexts" in event and "runtime" in event["contexts"]:
        if "env" in event["contexts"]["runtime"]:
            env = event["contexts"]["runtime"]["env"]
            sensitive_env = [
                "DATABASE_URL",
                "REDIS_URL",
                "SECRET_KEY",
                "GEMINI_API_KEY",
            ]
            for key in sensitive_env:
                if key in env:
                    env[key] = "[Filtered]"

    return event


def init_monitoring() -> None:
    """
    Initialize Sentry monitoring for production environment.

    Only initializes if SENTRY_DSN is set and environment is production.
    Configures integrations for FastAPI, SQLAlchemy, Redis, and Celery.
    """
    if not settings.SENTRY_DSN:
        logger.info("Sentry DSN not configured, skipping monitoring initialization")
        return

    if settings.ENVIRONMENT != "production":
        logger.info(
            f"Skipping Sentry initialization in {settings.ENVIRONMENT} environment"
        )
        return

    try:
        # Configure logging integration
        sentry_logging = LoggingIntegration(
            level=logging.INFO,  # Capture info and above as breadcrumbs
            event_level=logging.ERROR,  # Send errors as events
        )

        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            environment=settings.ENVIRONMENT,
            integrations=[
                FastApiIntegration(transaction_style="url"),
                SqlalchemyIntegration(),
                RedisIntegration(),
                CeleryIntegration(),
                sentry_logging,
            ],
            # Performance Monitoring
            traces_sample_rate=getattr(
                settings, "SENTRY_TRACES_SAMPLE_RATE", 0.1
            ),  # 10% of transactions
            profiles_sample_rate=getattr(
                settings, "SENTRY_PROFILES_SAMPLE_RATE", 0.1
            ),  # 10% for profiling
            # Privacy
            send_default_pii=False,  # Don't send personally identifiable information
            before_send=filter_sensitive_data,
            # Error filtering
            ignore_errors=[
                KeyboardInterrupt,
                "ConnectionRefusedError",
            ],
            # Release tracking
            release=getattr(settings, "APP_VERSION", None),
        )

        logger.info("Sentry monitoring initialized successfully")

    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")


def capture_exception(
    error: Exception, context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Manually capture an exception to Sentry with optional context.

    Args:
        error: Exception to capture
        context: Additional context dict
    """
    with sentry_sdk.push_scope() as scope:
        if context:
            for key, value in context.items():
                scope.set_extra(key, value)
        sentry_sdk.capture_exception(error)


def capture_message(
    message: str,
    level: Literal["fatal", "critical", "error", "warning", "info", "debug"] = "info",
    context: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Manually capture a message to Sentry.

    Args:
        message: Message to capture
        level: Severity level (info, warning, error, fatal)
        context: Additional context dict
    """
    with sentry_sdk.push_scope() as scope:
        if context:
            for key, value in context.items():
                scope.set_extra(key, value)
        sentry_sdk.capture_message(message, level=level)


def set_user_context(user_id: str, email: Optional[str] = None) -> None:
    """
    Set user context for Sentry events.

    Args:
        user_id: User ID
        email: User email (optional)
    """
    sentry_sdk.set_user(
        {
            "id": user_id,
            "email": email,
        }
    )


def clear_user_context() -> None:
    """Clear user context from Sentry."""
    sentry_sdk.set_user(None)
