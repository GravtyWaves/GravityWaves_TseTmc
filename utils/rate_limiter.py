import time
import threading
import logging
from collections import defaultdict, deque
from typing import Dict, Any, Optional
from functools import wraps

logger = logging.getLogger(__name__)

class RateLimiter:
    """
    Token bucket rate limiter implementation
    """

    def __init__(self, rate: float, capacity: int):
        """
        Initialize rate limiter

        Args:
            rate: Tokens added per second
            capacity: Maximum number of tokens in bucket
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_update = time.time()
        self.lock = threading.Lock()

    def _refill_tokens(self):
        """Refill tokens based on elapsed time"""
        now = time.time()
        elapsed = now - self.last_update
        tokens_to_add = elapsed * self.rate

        with self.lock:
            self.tokens = min(self.capacity, self.tokens + tokens_to_add)
            self.last_update = now

    def acquire(self, tokens: int = 1) -> bool:
        """
        Try to acquire tokens from the bucket

        Args:
            tokens: Number of tokens to acquire

        Returns:
            True if tokens were acquired, False otherwise
        """
        if tokens <= 0:
            return False

        self._refill_tokens()

        with self.lock:
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False

    def wait_for_tokens(self, tokens: int = 1) -> float:
        """
        Wait until tokens are available and acquire them

        Args:
            tokens: Number of tokens to acquire

        Returns:
            Time waited in seconds
        """
        if tokens <= 0:
            return 0.0

        start_time = time.time()

        while not self.acquire(tokens):
            # Calculate wait time for next token
            if self.rate > 0:
                wait_time = max(0.001, (tokens - self.tokens) / self.rate)
            else:
                wait_time = 1.0  # Wait 1 second when rate is zero (will be interrupted by test)
            time.sleep(wait_time)

        return time.time() - start_time

class SlidingWindowRateLimiter:
    """
    Sliding window rate limiter using fixed time windows
    """

    def __init__(self, max_requests: int, window_seconds: int):
        """
        Initialize sliding window rate limiter

        Args:
            max_requests: Maximum requests per window
            window_seconds: Window size in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()
        self.lock = threading.Lock()

    def acquire(self) -> bool:
        """
        Try to acquire permission for a request

        Returns:
            True if request is allowed, False otherwise
        """
        now = time.time()

        with self.lock:
            # Remove old requests outside the window
            while self.requests and now - self.requests[0] > self.window_seconds:
                self.requests.popleft()

            # Check if we can add a new request
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True

            return False

    def wait_for_slot(self) -> float:
        """
        Wait until a request slot is available

        Returns:
            Time waited in seconds
        """
        start_time = time.time()

        while not self.acquire():
            # Wait until oldest request expires
            if self.requests:
                wait_time = max(0.001, self.window_seconds - (time.time() - self.requests[0]))
                time.sleep(wait_time)
            else:
                time.sleep(0.001)  # Small delay if no requests

        return time.time() - start_time

class APIRateLimiter:
    """
    Specialized rate limiter for API endpoints with different limits per endpoint
    """

    def __init__(self):
        # Default rate limits per endpoint type
        self.endpoint_limits = {
            'search': {'rate': 10, 'capacity': 20},  # 10 requests/second, burst 20
            'list': {'rate': 5, 'capacity': 10},     # 5 requests/second, burst 10
            'history': {'rate': 2, 'capacity': 5},   # 2 requests/second, burst 5
            'details': {'rate': 20, 'capacity': 50}, # 20 requests/second, burst 50
            'default': {'rate': 10, 'capacity': 20}  # Default limits
        }

        self.limiters: Dict[str, RateLimiter] = {}

    def get_limiter(self, endpoint: str) -> RateLimiter:
        """Get or create rate limiter for specific endpoint"""
        if endpoint not in self.limiters:
            # Determine endpoint type
            endpoint_type = 'default'
            if 'search' in endpoint.lower() or 'instrument' in endpoint.lower():
                endpoint_type = 'search'
            elif 'list' in endpoint.lower() or 'index' in endpoint.lower():
                endpoint_type = 'list'
            elif 'history' in endpoint.lower() or 'price' in endpoint.lower():
                endpoint_type = 'history'
            elif 'details' in endpoint.lower() or 'info' in endpoint.lower():
                endpoint_type = 'details'

            limits = self.endpoint_limits[endpoint_type]
            self.limiters[endpoint] = RateLimiter(limits['rate'], limits['capacity'])

        return self.limiters[endpoint]

    def acquire(self, endpoint: str, tokens: int = 1) -> bool:
        """
        Try to acquire rate limit permission for endpoint

        Args:
            endpoint: API endpoint
            tokens: Number of tokens to acquire

        Returns:
            True if allowed, False if rate limited
        """
        limiter = self.get_limiter(endpoint)
        return limiter.acquire(tokens)

    def wait_for_slot(self, endpoint: str, tokens: int = 1) -> float:
        """
        Wait for rate limit slot to become available

        Args:
            endpoint: API endpoint
            tokens: Number of tokens to acquire

        Returns:
            Time waited in seconds
        """
        limiter = self.get_limiter(endpoint)
        return limiter.wait_for_tokens(tokens)

    def get_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all rate limiters"""
        status = {}
        for endpoint, limiter in self.limiters.items():
            limiter._refill_tokens()  # Update tokens
            status[endpoint] = {
                'tokens': limiter.tokens,
                'capacity': limiter.capacity,
                'rate': limiter.rate,
                'last_update': limiter.last_update
            }
        return status

class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded"""
    pass

def rate_limit(rate: float, capacity: int, wait: bool = False):
    """
    Decorator for applying rate limiting to functions

    Args:
        rate: Tokens per second
        capacity: Token bucket capacity
        wait: If True, wait for tokens; if False, raise exception
    """
    def decorator(func):
        limiter = RateLimiter(rate, capacity)

        @wraps(func)
        def wrapper(*args, **kwargs):
            if wait:
                limiter.wait_for_tokens()
            else:
                if not limiter.acquire():
                    raise RateLimitExceeded(f"Rate limit exceeded for {func.__name__}")
            return func(*args, **kwargs)

        return wrapper

    return decorator

# Global API rate limiter instance
api_rate_limiter = APIRateLimiter()
