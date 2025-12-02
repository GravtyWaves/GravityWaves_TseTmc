import time
import logging
from enum import Enum
from typing import Callable, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)

class CircuitBreakerState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"         # Circuit is open, failing fast
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreakerOpenException(Exception):
    """Exception raised when circuit breaker is open"""
    pass

class CircuitBreaker:
    """
    Circuit Breaker pattern implementation for API resilience

    States:
    - CLOSED: Normal operation, requests pass through
    - OPEN: Circuit is open, requests fail fast
    - HALF_OPEN: Testing if service has recovered
    """

    def __init__(self,
                 failure_threshold: int = 5,
                 recovery_timeout: int = 60,
                 expected_exception: Exception = Exception,
                 name: str = "CircuitBreaker"):
        """
        Initialize Circuit Breaker

        Args:
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Time in seconds to wait before trying again
            expected_exception: Exception type to monitor
            name: Name for logging purposes
        """
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        self.name = name

        # State management
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None

        # Metrics
        self.success_count = 0
        self.failure_count_total = 0

    def _can_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return True
        return time.time() - self.last_failure_time >= self.recovery_timeout

    def _record_success(self):
        """Record a successful call"""
        self.success_count += 1
        if self.state == CircuitBreakerState.HALF_OPEN:
            logger.info(f"CircuitBreaker '{self.name}': Service recovered, closing circuit")
            self.state = CircuitBreakerState.CLOSED
            self.failure_count = 0

    def _record_failure(self):
        """Record a failed call"""
        self.failure_count += 1
        self.failure_count_total += 1
        self.last_failure_time = time.time()

        if self.state == CircuitBreakerState.HALF_OPEN:
            logger.warning(f"CircuitBreaker '{self.name}': Service still failing, keeping circuit open")
            self.state = CircuitBreakerState.OPEN
        elif self.failure_count >= self.failure_threshold:
            logger.warning(f"CircuitBreaker '{self.name}': Failure threshold reached ({self.failure_count}), opening circuit")
            self.state = CircuitBreakerState.OPEN

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker

        Args:
            func: Function to call
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function

        Returns:
            Function result

        Raises:
            CircuitBreakerOpenException: If circuit is open
        """
        if self.state == CircuitBreakerState.OPEN:
            if self._can_attempt_reset():
                logger.info(f"CircuitBreaker '{self.name}': Attempting to reset circuit")
                self.state = CircuitBreakerState.HALF_OPEN
            else:
                raise CircuitBreakerOpenException(f"CircuitBreaker '{self.name}' is OPEN")

        try:
            result = func(*args, **kwargs)
            self._record_success()
            return result
        except self.expected_exception as e:
            self._record_failure()
            raise e

    def get_status(self) -> dict:
        """Get current status of circuit breaker"""
        return {
            'name': self.name,
            'state': self.state.value,
            'failure_count': self.failure_count,
            'success_count': self.success_count,
            'total_failures': self.failure_count_total,
            'last_failure': self.last_failure_time,
            'can_attempt_reset': self._can_attempt_reset()
        }

def circuit_breaker(failure_threshold: int = 5,
                   recovery_timeout: int = 60,
                   expected_exception: Exception = Exception,
                   name: Optional[str] = None):
    """
    Decorator for applying circuit breaker pattern to functions

    Args:
        failure_threshold: Number of failures before opening circuit
        recovery_timeout: Time in seconds to wait before trying again
        expected_exception: Exception type to monitor
        name: Name for circuit breaker (defaults to function name)
    """
    def decorator(func):
        cb_name = name or f"{func.__module__}.{func.__name__}"
        cb = CircuitBreaker(failure_threshold, recovery_timeout, expected_exception, cb_name)

        @wraps(func)
        def wrapper(*args, **kwargs):
            return cb.call(func, *args, **kwargs)

        # Attach circuit breaker to function for monitoring
        wrapper.circuit_breaker = cb
        return wrapper

    return decorator

class APICircuitBreaker:
    """
    Specialized circuit breaker for API endpoints
    """

    def __init__(self, base_failure_threshold: int = 3, base_recovery_timeout: int = 30):
        self.circuit_breakers = {}
        self.base_failure_threshold = base_failure_threshold
        self.base_recovery_timeout = base_recovery_timeout

    def get_circuit_breaker(self, endpoint: str) -> CircuitBreaker:
        """Get or create circuit breaker for specific endpoint"""
        if endpoint not in self.circuit_breakers:
            # Different endpoints can have different thresholds
            if 'price' in endpoint.lower() or 'history' in endpoint.lower():
                # History endpoints are more critical, lower threshold
                threshold = self.base_failure_threshold - 1
                timeout = self.base_recovery_timeout
            elif 'search' in endpoint.lower() or 'list' in endpoint.lower():
                # List endpoints are important but can be more tolerant
                threshold = self.base_failure_threshold + 1
                timeout = self.base_recovery_timeout * 2
            else:
                threshold = self.base_failure_threshold
                timeout = self.base_recovery_timeout

            self.circuit_breakers[endpoint] = CircuitBreaker(
                failure_threshold=threshold,
                recovery_timeout=timeout,
                expected_exception=Exception,
                name=f"API-{endpoint}"
            )

        return self.circuit_breakers[endpoint]

    def get_all_status(self) -> dict:
        """Get status of all circuit breakers"""
        return {
            endpoint: cb.get_status()
            for endpoint, cb in self.circuit_breakers.items()
        }

    def reset_all(self):
        """Reset all circuit breakers to closed state"""
        for cb in self.circuit_breakers.values():
            cb.state = CircuitBreakerState.CLOSED
            cb.failure_count = 0
            cb.last_failure_time = None
        logger.info("All API circuit breakers reset")

# Global API circuit breaker instance
api_circuit_breaker = APICircuitBreaker()
