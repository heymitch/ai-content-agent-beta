"""
Retry Decorator with Exponential Backoff
Conservative settings to minimize support tickets
"""
import asyncio
import logging
from functools import wraps
from typing import Callable, Any, Optional, Dict
import time

logger = logging.getLogger(__name__)


def async_retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 8.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    context_provider: Optional[Callable[[], Dict[str, Any]]] = None
):
    """
    Retry decorator with exponential backoff for async functions.

    Conservative settings:
    - max_retries: 3 (not unlimited)
    - Backoff: 1s, 2s, 4s, 8s (capped at 8s)
    - Logs full context on each retry

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        initial_delay: Initial delay in seconds (default: 1.0)
        max_delay: Maximum delay cap in seconds (default: 8.0)
        backoff_factor: Multiplier for each retry (default: 2.0)
        exceptions: Tuple of exceptions to catch (default: all Exception)
        context_provider: Optional function returning context dict for logging

    Example:
        @async_retry_with_backoff(
            max_retries=3,
            exceptions=(ConnectionError, TimeoutError)
        )
        async def my_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            delay = initial_delay

            for attempt in range(max_retries + 1):  # +1 because 0-indexed
                try:
                    # Get context for logging if provider given
                    context = context_provider() if context_provider else {}

                    if attempt > 0:
                        # Log retry attempt with full context
                        logger.warning(
                            f"🔄 Retry attempt {attempt}/{max_retries} for {func.__name__}",
                            extra={
                                'function': func.__name__,
                                'attempt': attempt,
                                'max_retries': max_retries,
                                'delay': delay,
                                'last_error': str(last_exception) if last_exception else None,
                                **context
                            }
                        )

                        # Wait before retry with exponential backoff
                        await asyncio.sleep(delay)

                        # Increase delay for next retry (capped at max_delay)
                        delay = min(delay * backoff_factor, max_delay)

                    # Attempt the function call
                    result = await func(*args, **kwargs)

                    # Success - log if it was a retry
                    if attempt > 0:
                        logger.info(
                            f"✅ Retry successful on attempt {attempt} for {func.__name__}",
                            extra={
                                'function': func.__name__,
                                'attempt': attempt,
                                **context
                            }
                        )

                    return result

                except exceptions as e:
                    last_exception = e
                    error_type = type(e).__name__

                    # Get context for logging
                    context = context_provider() if context_provider else {}

                    if attempt >= max_retries:
                        # Final failure - log with full context
                        logger.error(
                            f"❌ All retry attempts exhausted for {func.__name__}",
                            extra={
                                'function': func.__name__,
                                'attempts': max_retries + 1,
                                'error_type': error_type,
                                'error_message': str(e),
                                **context
                            },
                            exc_info=True
                        )
                        raise
                    else:
                        # Log transient failure
                        logger.warning(
                            f"⚠️  Transient error in {func.__name__}: {error_type}",
                            extra={
                                'function': func.__name__,
                                'attempt': attempt,
                                'error_type': error_type,
                                'error_message': str(e),
                                'will_retry': True,
                                'next_delay': delay,
                                **context
                            }
                        )

            # Should never reach here, but just in case
            if last_exception:
                raise last_exception

        return wrapper
    return decorator


def sync_retry_with_backoff(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 8.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,),
    context_provider: Optional[Callable[[], Dict[str, Any]]] = None
):
    """
    Retry decorator with exponential backoff for sync functions.

    Same logic as async_retry_with_backoff but for synchronous functions.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            delay = initial_delay

            for attempt in range(max_retries + 1):
                try:
                    context = context_provider() if context_provider else {}

                    if attempt > 0:
                        logger.warning(
                            f"🔄 Retry attempt {attempt}/{max_retries} for {func.__name__}",
                            extra={
                                'function': func.__name__,
                                'attempt': attempt,
                                'max_retries': max_retries,
                                'delay': delay,
                                'last_error': str(last_exception) if last_exception else None,
                                **context
                            }
                        )

                        time.sleep(delay)
                        delay = min(delay * backoff_factor, max_delay)

                    result = func(*args, **kwargs)

                    if attempt > 0:
                        logger.info(
                            f"✅ Retry successful on attempt {attempt} for {func.__name__}",
                            extra={
                                'function': func.__name__,
                                'attempt': attempt,
                                **context
                            }
                        )

                    return result

                except exceptions as e:
                    last_exception = e
                    error_type = type(e).__name__
                    context = context_provider() if context_provider else {}

                    if attempt >= max_retries:
                        logger.error(
                            f"❌ All retry attempts exhausted for {func.__name__}",
                            extra={
                                'function': func.__name__,
                                'attempts': max_retries + 1,
                                'error_type': error_type,
                                'error_message': str(e),
                                **context
                            },
                            exc_info=True
                        )
                        raise
                    else:
                        logger.warning(
                            f"⚠️  Transient error in {func.__name__}: {error_type}",
                            extra={
                                'function': func.__name__,
                                'attempt': attempt,
                                'error_type': error_type,
                                'error_message': str(e),
                                'will_retry': True,
                                'next_delay': delay,
                                **context
                            }
                        )

            if last_exception:
                raise last_exception

        return wrapper
    return decorator


# Common exception types to retry
RETRIABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    OSError,  # Covers network-related OS errors
    # Add SDK-specific exceptions if available
)


# Helper to check if an exception is retriable
def is_retriable_error(exception: Exception) -> bool:
    """
    Determine if an exception should be retried.

    Retriable errors:
    - ConnectionError, TimeoutError
    - Network-related OSErrors
    - Exceptions with "connection", "timeout", "network" in message

    Non-retriable errors:
    - ValueError, TypeError (code bugs)
    - PermissionError (auth issues)
    - Exceptions with "invalid", "forbidden" in message
    """
    error_type = type(exception).__name__
    error_message = str(exception).lower()

    # Check exception type
    if isinstance(exception, RETRIABLE_EXCEPTIONS):
        return True

    # Check error message for retriable keywords
    retriable_keywords = ['connection', 'timeout', 'network', 'unavailable', 'refused']
    if any(keyword in error_message for keyword in retriable_keywords):
        return True

    # Check error message for non-retriable keywords
    non_retriable_keywords = ['invalid', 'forbidden', 'permission', 'unauthorized', 'not found']
    if any(keyword in error_message for keyword in non_retriable_keywords):
        return False

    # Default: retry unknown errors (conservative for production)
    return True
