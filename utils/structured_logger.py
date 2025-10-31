"""
Structured Logging with Full Context
Uses structlog for consistent, JSON-formatted logs with context fields
"""
import structlog
import logging
import sys
from typing import Dict, Any, Optional


def configure_structured_logging(log_level: str = "INFO"):
    """
    Configure structlog for the application.

    Logs JSON format with context fields:
    - timestamp
    - level
    - event (message)
    - logger
    - Plus any custom fields (user_id, thread_ts, platform, etc.)

    Args:
        log_level: Logging level (default: INFO)
    """
    # Configure stdlib logging to work with structlog
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Configure structlog
    structlog.configure(
        processors=[
            # Add log level
            structlog.stdlib.add_log_level,
            # Add logger name
            structlog.stdlib.add_logger_name,
            # Add timestamp
            structlog.processors.TimeStamper(fmt="iso"),
            # Stack trace for exceptions
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            # Render as JSON
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog logger

    Example:
        logger = get_logger(__name__)
        logger.info("Operation started", user_id="U123", operation="create_post")
    """
    return structlog.get_logger(name)


def log_error(
    logger: structlog.BoundLogger,
    message: str,
    error: Exception,
    context: Optional[Dict[str, Any]] = None,
    **extra
):
    """
    Log an error with full context.

    Args:
        logger: Structured logger instance
        message: Error message
        error: Exception object
        context: Optional context dict (user_id, thread_ts, platform, etc.)
        **extra: Additional fields to log

    Example:
        log_error(
            logger,
            "LinkedIn post creation failed",
            error=e,
            context={"user_id": "U123", "thread_ts": "1234.5678"},
            platform="linkedin",
            operation="create_post"
        )
    """
    error_info = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        **(context or {}),
        **extra
    }

    logger.error(message, **error_info, exc_info=True)


def log_operation_start(
    logger: structlog.BoundLogger,
    operation: str,
    context: Optional[Dict[str, Any]] = None,
    **extra
):
    """
    Log the start of an operation with context.

    Args:
        logger: Structured logger instance
        operation: Operation name
        context: Optional context dict
        **extra: Additional fields

    Example:
        log_operation_start(
            logger,
            "create_linkedin_post",
            context={"user_id": "U123", "thread_ts": "1234.5678"},
            topic="AI automation"
        )
    """
    logger.info(
        f"▶️  Starting {operation}",
        operation=operation,
        stage="start",
        **(context or {}),
        **extra
    )


def log_operation_end(
    logger: structlog.BoundLogger,
    operation: str,
    duration: float,
    success: bool,
    context: Optional[Dict[str, Any]] = None,
    **extra
):
    """
    Log the end of an operation with timing.

    Args:
        logger: Structured logger instance
        operation: Operation name
        duration: Duration in seconds
        success: Whether operation succeeded
        context: Optional context dict
        **extra: Additional fields (result, quality_score, etc.)

    Example:
        log_operation_end(
            logger,
            "create_linkedin_post",
            duration=15.3,
            success=True,
            context={"user_id": "U123", "thread_ts": "1234.5678"},
            quality_score=22
        )
    """
    log_func = logger.info if success else logger.error
    status = "✅ completed" if success else "❌ failed"

    log_func(
        f"{status} {operation}",
        operation=operation,
        stage="end",
        duration=f"{duration:.2f}s",
        success=success,
        **(context or {}),
        **extra
    )


def create_context(
    user_id: Optional[str] = None,
    thread_ts: Optional[str] = None,
    channel_id: Optional[str] = None,
    platform: Optional[str] = None,
    session_id: Optional[str] = None,
    **extra
) -> Dict[str, Any]:
    """
    Create a context dict for logging.

    Filters out None values.

    Args:
        user_id: Slack user ID
        thread_ts: Slack thread timestamp
        channel_id: Slack channel ID
        platform: Content platform (linkedin, twitter, etc.)
        session_id: Agent session ID
        **extra: Additional context fields

    Returns:
        Context dict with non-None values

    Example:
        context = create_context(
            user_id="U123",
            thread_ts="1234.5678",
            platform="linkedin"
        )
    """
    context = {
        'user_id': user_id,
        'thread_ts': thread_ts,
        'channel_id': channel_id,
        'platform': platform,
        'session_id': session_id,
        **extra
    }

    # Filter out None values
    return {k: v for k, v in context.items() if v is not None}


# Convenience logger for quick use
# Configure on first import
try:
    configure_structured_logging()
except Exception:
    # Fall back to standard logging if structlog fails
    pass

# Default logger for utils
default_logger = get_logger("agent")


def log_retry_attempt(
    operation: str,
    attempt: int,
    max_retries: int,
    delay: float,
    error: Exception,
    context: Optional[Dict[str, Any]] = None
):
    """
    Log a retry attempt with full context.

    Args:
        operation: Operation being retried
        attempt: Current attempt number (1-indexed)
        max_retries: Maximum retry attempts
        delay: Delay before next retry in seconds
        error: Exception that triggered retry
        context: Optional context dict

    Example:
        log_retry_attempt(
            "sdk_connect",
            attempt=2,
            max_retries=3,
            delay=4.0,
            error=connection_error,
            context={"session_id": "abc123"}
        )
    """
    default_logger.warning(
        f"🔄 Retrying {operation} (attempt {attempt}/{max_retries})",
        operation=operation,
        attempt=attempt,
        max_retries=max_retries,
        next_delay=f"{delay:.1f}s",
        error_type=type(error).__name__,
        error_message=str(error),
        **(context or {})
    )


def log_circuit_breaker_event(
    circuit_name: str,
    event: str,
    state: str,
    failure_count: int,
    context: Optional[Dict[str, Any]] = None,
    **extra
):
    """
    Log a circuit breaker event.

    Args:
        circuit_name: Circuit breaker name
        event: Event type (opened, closed, half_open, rejected)
        state: Current state
        failure_count: Current failure count
        context: Optional context dict
        **extra: Additional fields

    Example:
        log_circuit_breaker_event(
            "linkedin_agent",
            event="opened",
            state="open",
            failure_count=3,
            context={"platform": "linkedin"}
        )
    """
    emoji_map = {
        'opened': '🔥',
        'closed': '✅',
        'half_open': '🔄',
        'rejected': '⛔'
    }

    emoji = emoji_map.get(event, '⚠️')

    default_logger.warning(
        f"{emoji} Circuit breaker '{circuit_name}' {event}",
        circuit_breaker=circuit_name,
        event=event,
        state=state,
        failure_count=failure_count,
        **(context or {}),
        **extra
    )
