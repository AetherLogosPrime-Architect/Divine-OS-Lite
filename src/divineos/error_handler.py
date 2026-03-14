"""
Error handling and retry logic for agent operations.
Implements exponential backoff, circuit breakers, and failure recovery.
"""

import logging
import time
from typing import Any, Callable, TypeVar
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ErrorType(Enum):
    """Classification of error types for retry decisions."""

    TRANSIENT = "transient"  # Retry (rate limit, timeout)
    PERMANENT = "permanent"  # Don't retry (auth, validation)
    UNKNOWN = "unknown"  # Retry with caution


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_factor: float = 2.0,
        jitter: bool = True,
    ) -> None:
        """
        Initialize retry configuration.

        Args:
            max_retries: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            max_delay: Maximum delay in seconds
            backoff_factor: Exponential backoff multiplier
            jitter: Add random jitter to delays
        """
        self.max_retries = max_retries
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter

    def get_delay(self, attempt: int) -> float:
        """
        Calculate delay for attempt with exponential backoff.

        Args:
            attempt: Attempt number (0-indexed)

        Returns:
            Delay in seconds
        """
        delay = self.initial_delay * (self.backoff_factor ** attempt)
        delay = min(delay, self.max_delay)

        if self.jitter:
            import random

            delay = delay * (0.5 + random.random())

        return delay


class CircuitBreaker:
    """Prevent cascading failures with circuit breaker pattern."""

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
    ) -> None:
        """
        Initialize circuit breaker.

        Args:
            failure_threshold: Failures before opening circuit
            recovery_timeout: Seconds before attempting recovery
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time: float | None = None
        self.is_open = False

    def record_success(self) -> None:
        """Record successful operation."""
        self.failure_count = 0
        self.is_open = False
        self.last_failure_time = None

    def record_failure(self) -> None:
        """Record failed operation."""
        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.failure_count >= self.failure_threshold:
            self.is_open = True
            logger.warning(
                f"Circuit breaker opened after {self.failure_count} failures"
            )

    def can_attempt(self) -> bool:
        """Check if operation can be attempted."""
        if not self.is_open:
            return True

        if self.last_failure_time is None:
            return True

        elapsed = time.time() - self.last_failure_time
        if elapsed >= self.recovery_timeout:
            self.is_open = False
            self.failure_count = 0
            logger.info("Circuit breaker attempting recovery")
            return True

        return False

    def get_status(self) -> dict[str, Any]:
        """Get circuit breaker status."""
        return {
            "is_open": self.is_open,
            "failure_count": self.failure_count,
            "failure_threshold": self.failure_threshold,
            "last_failure_time": self.last_failure_time,
        }


class ErrorHandler:
    """Handle errors with retry logic and circuit breaker."""

    def __init__(
        self,
        retry_config: RetryConfig | None = None,
        circuit_breaker: CircuitBreaker | None = None,
    ) -> None:
        """
        Initialize error handler.

        Args:
            retry_config: Retry configuration
            circuit_breaker: Circuit breaker instance
        """
        self.retry_config = retry_config or RetryConfig()
        self.circuit_breaker = circuit_breaker or CircuitBreaker()
        self.error_count = 0
        self.success_count = 0

    def classify_error(self, error: Exception) -> ErrorType:
        """
        Classify error for retry decision.

        Args:
            error: Exception to classify

        Returns:
            ErrorType classification
        """
        error_msg = str(error).lower()

        # Transient errors - retry
        transient_keywords = [
            "timeout",
            "rate limit",
            "429",
            "503",
            "temporarily",
            "connection reset",
            "temporarily unavailable",
        ]
        if any(keyword in error_msg for keyword in transient_keywords):
            return ErrorType.TRANSIENT

        # Permanent errors - don't retry
        permanent_keywords = [
            "unauthorized",
            "forbidden",
            "401",
            "403",
            "invalid",
            "not found",
            "404",
            "bad request",
            "400",
        ]
        if any(keyword in error_msg for keyword in permanent_keywords):
            return ErrorType.PERMANENT

        return ErrorType.UNKNOWN

    def execute_with_retry(
        self,
        func: Callable[..., T],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """
        Execute function with retry logic.

        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments

        Returns:
            Function result

        Raises:
            Exception: If all retries exhausted
        """
        if not self.circuit_breaker.can_attempt():
            raise RuntimeError(
                "Circuit breaker is open - operation blocked"
            )

        last_error: Exception | None = None

        for attempt in range(self.retry_config.max_retries + 1):
            try:
                result = func(*args, **kwargs)
                self.circuit_breaker.record_success()
                self.success_count += 1
                logger.info(
                    f"Operation succeeded on attempt {attempt + 1}"
                )
                return result

            except Exception as e:
                last_error = e
                error_type = self.classify_error(e)
                self.error_count += 1
                self.circuit_breaker.record_failure()

                # Don't retry permanent errors
                if error_type == ErrorType.PERMANENT:
                    logger.error(
                        f"Permanent error - not retrying: {str(e)}"
                    )
                    raise

                # Last attempt
                if attempt >= self.retry_config.max_retries:
                    logger.error(
                        f"All {self.retry_config.max_retries + 1} attempts "
                        f"exhausted: {str(e)}"
                    )
                    raise

                # Calculate delay and retry
                delay = self.retry_config.get_delay(attempt)
                logger.warning(
                    f"Attempt {attempt + 1} failed ({error_type.value}), "
                    f"retrying in {delay:.1f}s: {str(e)}"
                )
                time.sleep(delay)

        # Should not reach here
        if last_error:
            raise last_error
        raise RuntimeError("Unexpected error in retry loop")

    def get_stats(self) -> dict[str, Any]:
        """Get error handler statistics."""
        total = self.success_count + self.error_count
        success_rate = (
            (self.success_count / total * 100) if total > 0 else 0
        )

        return {
            "total_operations": total,
            "successes": self.success_count,
            "errors": self.error_count,
            "success_rate": success_rate,
            "circuit_breaker": self.circuit_breaker.get_status(),
        }

    def reset_stats(self) -> None:
        """Reset statistics."""
        self.error_count = 0
        self.success_count = 0
