"""
Circuit Breaker Pattern
Conservative settings: 3 failures → 120s cooldown
Prevents cascading failures when API is degraded
"""
import time
import logging
from functools import wraps
from typing import Callable, Any, Optional, Dict
from enum import Enum
from threading import Lock

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Circuit tripped, rejecting requests
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker to prevent cascading failures.

    Conservative settings:
    - 3 consecutive failures → circuit opens for 120s
    - After 120s → half-open (try 1 request)
    - If successful → close circuit
    - If fails → re-open for 120s

    Thread-safe implementation.
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        recovery_timeout: float = 120.0,
        name: str = "circuit_breaker"
    ):
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Number of failures before opening (default: 3)
            recovery_timeout: Seconds to wait before trying again (default: 120)
            name: Name for logging
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name

        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

        self._lock = Lock()

    def call(self, func: Callable, *args, context: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
        """
        Call function through circuit breaker (synchronous version).

        Args:
            func: Function to call
            *args: Positional arguments for function
            context: Optional context dict for logging
            **kwargs: Keyword arguments for function

        Returns:
            Result of function call

        Raises:
            CircuitBreakerOpen: If circuit is open
            Exception: Any exception from the function
        """
        with self._lock:
            if self.state == CircuitState.OPEN:
                # Check if recovery timeout has elapsed
                if time.time() - self.last_failure_time >= self.recovery_timeout:
                    logger.info(
                        f"🔄 Circuit breaker '{self.name}' entering HALF_OPEN state (testing recovery)",
                        extra={
                            'circuit_breaker': self.name,
                            'state': 'half_open',
                            'failure_count': self.failure_count,
                            **(context or {})
                        }
                    )
                    self.state = CircuitState.HALF_OPEN
                else:
                    # Circuit still open - reject request
                    time_remaining = self.recovery_timeout - (time.time() - self.last_failure_time)
                    logger.warning(
                        f"⛔ Circuit breaker '{self.name}' is OPEN - rejecting request",
                        extra={
                            'circuit_breaker': self.name,
                            'state': 'open',
                            'time_remaining': f"{time_remaining:.1f}s",
                            'failure_count': self.failure_count,
                            **(context or {})
                        }
                    )
                    raise CircuitBreakerOpen(
                        f"Circuit breaker '{self.name}' is open. "
                        f"Retry in {time_remaining:.1f}s"
                    )

        # Try to call the function
        try:
            result = func(*args, **kwargs)

            # Success - reset or close circuit
            with self._lock:
                if self.state == CircuitState.HALF_OPEN:
                    logger.info(
                        f"✅ Circuit breaker '{self.name}' test successful - CLOSING circuit",
                        extra={
                            'circuit_breaker': self.name,
                            'state': 'closed',
                            'previous_failures': self.failure_count,
                            **(context or {})
                        }
                    )

                self.failure_count = 0
                self.state = CircuitState.CLOSED

            return result

        except Exception as e:
            # Failure - increment counter and potentially open circuit
            with self._lock:
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.state == CircuitState.HALF_OPEN:
                    # Failed during test - re-open circuit
                    logger.error(
                        f"❌ Circuit breaker '{self.name}' test failed - RE-OPENING circuit",
                        extra={
                            'circuit_breaker': self.name,
                            'state': 'open',
                            'failure_count': self.failure_count,
                            'recovery_timeout': f"{self.recovery_timeout}s",
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            **(context or {})
                        }
                    )
                    self.state = CircuitState.OPEN

                elif self.failure_count >= self.failure_threshold:
                    # Reached threshold - open circuit
                    logger.error(
                        f"🔥 Circuit breaker '{self.name}' OPENING - failure threshold reached",
                        extra={
                            'circuit_breaker': self.name,
                            'state': 'open',
                            'failure_count': self.failure_count,
                            'failure_threshold': self.failure_threshold,
                            'recovery_timeout': f"{self.recovery_timeout}s",
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            **(context or {})
                        }
                    )
                    self.state = CircuitState.OPEN

                else:
                    # Increment but don't open yet
                    logger.warning(
                        f"⚠️  Circuit breaker '{self.name}' failure {self.failure_count}/{self.failure_threshold}",
                        extra={
                            'circuit_breaker': self.name,
                            'state': 'closed',
                            'failure_count': self.failure_count,
                            'failure_threshold': self.failure_threshold,
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            **(context or {})
                        }
                    )

            raise

    async def call_async(self, func: Callable, *args, context: Optional[Dict[str, Any]] = None, **kwargs) -> Any:
        """
        Call async function through circuit breaker (async version).

        Args:
            func: Async function to call
            *args: Positional arguments for function
            context: Optional context dict for logging
            **kwargs: Keyword arguments for function

        Returns:
            Result of function call

        Raises:
            CircuitBreakerOpen: If circuit is open
            Exception: Any exception from the function
        """
        with self._lock:
            if self.state == CircuitState.OPEN:
                # Check if recovery timeout has elapsed
                if time.time() - self.last_failure_time >= self.recovery_timeout:
                    logger.info(
                        f"🔄 Circuit breaker '{self.name}' entering HALF_OPEN state (testing recovery)",
                        extra={
                            'circuit_breaker': self.name,
                            'state': 'half_open',
                            'failure_count': self.failure_count,
                            **(context or {})
                        }
                    )
                    self.state = CircuitState.HALF_OPEN
                else:
                    # Circuit still open - reject request
                    time_remaining = self.recovery_timeout - (time.time() - self.last_failure_time)
                    logger.warning(
                        f"⛔ Circuit breaker '{self.name}' is OPEN - rejecting request",
                        extra={
                            'circuit_breaker': self.name,
                            'state': 'open',
                            'time_remaining': f"{time_remaining:.1f}s",
                            'failure_count': self.failure_count,
                            **(context or {})
                        }
                    )
                    raise CircuitBreakerOpen(
                        f"Circuit breaker '{self.name}' is open. "
                        f"Retry in {time_remaining:.1f}s"
                    )

        # Try to call the async function
        try:
            result = await func(*args, **kwargs)

            # Success - reset or close circuit
            with self._lock:
                if self.state == CircuitState.HALF_OPEN:
                    logger.info(
                        f"✅ Circuit breaker '{self.name}' test successful - CLOSING circuit",
                        extra={
                            'circuit_breaker': self.name,
                            'state': 'closed',
                            'previous_failures': self.failure_count,
                            **(context or {})
                        }
                    )

                self.failure_count = 0
                self.state = CircuitState.CLOSED

            return result

        except Exception as e:
            # Failure - increment counter and potentially open circuit
            with self._lock:
                self.failure_count += 1
                self.last_failure_time = time.time()

                if self.state == CircuitState.HALF_OPEN:
                    # Failed during test - re-open circuit
                    logger.error(
                        f"❌ Circuit breaker '{self.name}' test failed - RE-OPENING circuit",
                        extra={
                            'circuit_breaker': self.name,
                            'state': 'open',
                            'failure_count': self.failure_count,
                            'recovery_timeout': f"{self.recovery_timeout}s",
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            **(context or {})
                        }
                    )
                    self.state = CircuitState.OPEN

                elif self.failure_count >= self.failure_threshold:
                    # Reached threshold - open circuit
                    logger.error(
                        f"🔥 Circuit breaker '{self.name}' OPENING - failure threshold reached",
                        extra={
                            'circuit_breaker': self.name,
                            'state': 'open',
                            'failure_count': self.failure_count,
                            'failure_threshold': self.failure_threshold,
                            'recovery_timeout': f"{self.recovery_timeout}s",
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            **(context or {})
                        }
                    )
                    self.state = CircuitState.OPEN

                else:
                    # Increment but don't open yet
                    logger.warning(
                        f"⚠️  Circuit breaker '{self.name}' failure {self.failure_count}/{self.failure_threshold}",
                        extra={
                            'circuit_breaker': self.name,
                            'state': 'closed',
                            'failure_count': self.failure_count,
                            'failure_threshold': self.failure_threshold,
                            'error_type': type(e).__name__,
                            'error_message': str(e),
                            **(context or {})
                        }
                    )

            raise

    def reset(self):
        """Manually reset circuit breaker to closed state."""
        with self._lock:
            logger.info(
                f"🔄 Manually resetting circuit breaker '{self.name}'",
                extra={
                    'circuit_breaker': self.name,
                    'state': 'closed',
                    'previous_failures': self.failure_count
                }
            )
            self.failure_count = 0
            self.state = CircuitState.CLOSED
            self.last_failure_time = None

    def get_state(self) -> Dict[str, Any]:
        """Get current circuit breaker state for monitoring."""
        with self._lock:
            return {
                'name': self.name,
                'state': self.state.value,
                'failure_count': self.failure_count,
                'failure_threshold': self.failure_threshold,
                'recovery_timeout': self.recovery_timeout,
                'last_failure_time': self.last_failure_time,
                'time_since_failure': time.time() - self.last_failure_time if self.last_failure_time else None
            }


class CircuitBreakerOpen(Exception):
    """Exception raised when circuit breaker is open."""
    pass


def circuit_breaker(
    failure_threshold: int = 3,
    recovery_timeout: float = 120.0,
    name: Optional[str] = None
):
    """
    Decorator to apply circuit breaker to a function.

    Args:
        failure_threshold: Number of failures before opening (default: 3)
        recovery_timeout: Seconds to wait before trying again (default: 120)
        name: Circuit breaker name (defaults to function name)

    Example:
        @circuit_breaker(failure_threshold=3, recovery_timeout=120)
        async def my_function():
            ...
    """
    def decorator(func: Callable) -> Callable:
        breaker_name = name or func.__name__
        breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            name=breaker_name
        )

        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            # Extract context if available (for logging)
            context = kwargs.pop('_circuit_breaker_context', None)

            # Call through circuit breaker (async version)
            return await breaker.call_async(func, *args, context=context, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            context = kwargs.pop('_circuit_breaker_context', None)
            return breaker.call(func, *args, context=context, **kwargs)

        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            async_wrapper._circuit_breaker = breaker
            return async_wrapper
        else:
            sync_wrapper._circuit_breaker = breaker
            return sync_wrapper

    return decorator
