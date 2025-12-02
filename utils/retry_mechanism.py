import time
import random
import logging
from typing import Callable, Any, Optional, Type, Union
from functools import wraps

logger = logging.getLogger(__name__)

class RetryError(Exception):
    """Exception raised when all retry attempts are exhausted"""
    def __init__(self, message: str, last_exception: Exception):
        super().__init__(message)
        self.last_exception = last_exception

class RetryConfig:
    """Configuration for retry behavior"""

    def __init__(self,
                 max_attempts: int = 3,
                 initial_delay: float = 1.0,
                 max_delay: float = 60.0,
                 backoff_factor: float = 2.0,
                 jitter: bool = True,
                 retry_on_exceptions: tuple = (Exception,),
                 retry_on_status_codes: tuple = (500, 502, 503, 504)):
        """
        Initialize retry configuration

        Args:
            max_attempts: Maximum number of retry attempts
            initial_delay: Initial delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            backoff_factor: Exponential backoff multiplier
            jitter: Whether to add random jitter to delay
            retry_on_exceptions: Tuple of exception types to retry on
            retry_on_status_codes: Tuple of HTTP status codes to retry on
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        self.jitter = jitter
        self.retry_on_exceptions = retry_on_exceptions
        self.retry_on_status_codes = retry_on_status_codes

class ExponentialBackoffRetry:
    """
    Retry mechanism with exponential backoff and jitter
    """

    def __init__(self, config: RetryConfig):
        self.config = config

    def _calculate_delay(self, attempt: int) -> float:
        """Calculate delay for the given attempt number"""
        delay = self.config.initial_delay * (self.config.backoff_factor ** attempt)
        delay = min(delay, self.config.max_delay)

        if self.config.jitter:
            # Add random jitter (±25% of delay)
            jitter_range = delay * 0.25
            delay += random.uniform(-jitter_range, jitter_range)

        return max(0.001, delay)  # Minimum 1ms delay

    def _should_retry(self, exception: Exception, status_code: Optional[int] = None) -> bool:
        """Determine if the operation should be retried"""
        # Check HTTP status codes first if provided
        if status_code is not None and status_code in self.config.retry_on_status_codes:
            return True

        # Check exception types only if no status codes are configured or status_code is None
        if status_code is None and isinstance(exception, self.config.retry_on_exceptions):
            return True

        return False

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retry logic

        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            RetryError: If all retry attempts are exhausted
        """
        last_exception = None

        for attempt in range(self.config.max_attempts):
            try:
                result = func(*args, **kwargs)
                return result

            except Exception as e:
                last_exception = e

                # Check if we should retry
                if attempt < self.config.max_attempts - 1 and self._should_retry(e):
                    delay = self._calculate_delay(attempt)
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay:.2f}s...")
                    time.sleep(delay)
                else:
                    # Don't retry or max attempts reached
                    break

        # All attempts exhausted
        raise RetryError(
            f"Operation failed after {self.config.max_attempts} attempts",
            last_exception
        )

class APIRetryConfig(RetryConfig):
    """Specialized retry config for API operations"""

    def __init__(self,
                 max_attempts: int = 5,
                 initial_delay: float = 1.0,
                 max_delay: float = 30.0,
                 backoff_factor: float = 1.5,
                 jitter: bool = True):
        # API-specific retry configuration
        retry_exceptions = (
            ConnectionError,
            TimeoutError,
            OSError,  # Network-related OS errors
        )

        retry_status_codes = (
            408,  # Request Timeout
            429,  # Too Many Requests
            500,  # Internal Server Error
            502,  # Bad Gateway
            503,  # Service Unavailable
            504,  # Gateway Timeout
        )

        super().__init__(
            max_attempts=max_attempts,
            initial_delay=initial_delay,
            max_delay=max_delay,
            backoff_factor=backoff_factor,
            jitter=jitter,
            retry_on_exceptions=retry_exceptions,
            retry_on_status_codes=retry_status_codes
        )

class CircuitBreakerAwareRetry(ExponentialBackoffRetry):
    """
    Retry mechanism that works with circuit breaker pattern
    """

    def __init__(self, config: RetryConfig, circuit_breaker=None):
        super().__init__(config)
        self.circuit_breaker = circuit_breaker

    def execute(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with retry logic, respecting circuit breaker state
        """
        if self.circuit_breaker:
            # Use circuit breaker to execute the operation
            return self.circuit_breaker.call(
                lambda: super(CircuitBreakerAwareRetry, self).execute(func, *args, **kwargs)
            )
        else:
            # Execute without circuit breaker
            return super(CircuitBreakerAwareRetry, self).execute(func, *args, **kwargs)

def retry_with_backoff(max_attempts: int = 3,
                      initial_delay: float = 1.0,
                      max_delay: float = 60.0,
                      backoff_factor: float = 2.0,
                      jitter: bool = True,
                      retry_on_exceptions: tuple = (Exception,),
                      retry_on_status_codes: tuple = (500, 502, 503, 504)):
    """
    Decorator for applying retry logic with exponential backoff

    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay between retries in seconds
        max_delay: Maximum delay between retries in seconds
        backoff_factor: Exponential backoff multiplier
        jitter: Whether to add random jitter to delay
        retry_on_exceptions: Tuple of exception types to retry on
        retry_on_status_codes: Tuple of HTTP status codes to retry on
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        max_delay=max_delay,
        backoff_factor=backoff_factor,
        jitter=jitter,
        retry_on_exceptions=retry_on_exceptions,
        retry_on_status_codes=retry_on_status_codes
    )

    def decorator(func):
        retry_instance = ExponentialBackoffRetry(config)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return retry_instance.execute(func, *args, **kwargs)

        return wrapper

    return decorator

def api_retry(max_attempts: int = 5,
              initial_delay: float = 1.0,
              max_delay: float = 30.0,
              backoff_factor: float = 1.5,
              jitter: bool = True):
    """
    Decorator specifically for API operations with appropriate defaults
    """
    return retry_with_backoff(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        max_delay=max_delay,
        backoff_factor=backoff_factor,
        jitter=jitter,
        retry_on_exceptions=(ConnectionError, TimeoutError, OSError),
        retry_on_status_codes=(408, 429, 500, 502, 503, 504)
    )

# Global retry instances
api_retry_config = APIRetryConfig()
api_retry_instance = ExponentialBackoffRetry(api_retry_config)
