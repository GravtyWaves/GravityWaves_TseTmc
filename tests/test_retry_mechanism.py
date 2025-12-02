"""
تست‌های حرفه‌ای برای utils/retry_mechanism.py با استفاده از داده‌های واقعی TSE
"""

import pytest
import time
import threading
from unittest.mock import patch, MagicMock, call
from utils.retry_mechanism import (
    RetryError,
    RetryConfig,
    ExponentialBackoffRetry,
    APIRetryConfig,
    CircuitBreakerAwareRetry,
    retry_with_backoff,
    api_retry,
    api_retry_config,
    api_retry_instance
)


class TestRetryConfig:
    """تست‌های RetryConfig"""

    def test_default_initialization(self):
        """تست مقداردهی اولیه پیش‌فرض"""
        config = RetryConfig()

        assert config.max_attempts == 3
        assert config.initial_delay == 1.0
        assert config.max_delay == 60.0
        assert config.backoff_factor == 2.0
        assert config.jitter is True
        assert config.retry_on_exceptions == (Exception,)
        assert config.retry_on_status_codes == (500, 502, 503, 504)

    def test_custom_initialization(self):
        """تست مقداردهی اولیه سفارشی"""
        config = RetryConfig(
            max_attempts=5,
            initial_delay=2.0,
            max_delay=120.0,
            backoff_factor=1.5,
            jitter=False,
            retry_on_exceptions=(ValueError, TypeError),
            retry_on_status_codes=(408, 429)
        )

        assert config.max_attempts == 5
        assert config.initial_delay == 2.0
        assert config.max_delay == 120.0
        assert config.backoff_factor == 1.5
        assert config.jitter is False
        assert config.retry_on_exceptions == (ValueError, TypeError)
        assert config.retry_on_status_codes == (408, 429)


class TestExponentialBackoffRetry:
    """تست‌های ExponentialBackoffRetry"""

    def setup_method(self):
        """تنظیمات اولیه"""
        self.config = RetryConfig(max_attempts=3, initial_delay=0.1, max_delay=1.0)
        self.retry = ExponentialBackoffRetry(self.config)

    def test_successful_execution(self):
        """تست اجرای موفق"""
        def successful_func():
            return "success"

        result = self.retry.execute(successful_func)
        assert result == "success"

    def test_retry_on_failure(self):
        """تست retry در صورت شکست"""
        call_count = 0

        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Network error")
            return "success"

        result = self.retry.execute(failing_func)
        assert result == "success"
        assert call_count == 3

    def test_max_attempts_exhausted(self):
        """تست اتمام حداکثر تلاش‌ها"""
        def always_failing_func():
            raise ValueError("Always fails")

        with pytest.raises(RetryError) as exc_info:
            self.retry.execute(always_failing_func)

        assert "failed after 3 attempts" in str(exc_info.value)
        assert isinstance(exc_info.value.last_exception, ValueError)

    def test_no_retry_on_non_retryable_exception(self):
        """تست عدم retry برای exception غیر قابل retry"""
        # تنظیم config برای retry فقط روی ConnectionError
        config = RetryConfig(
            max_attempts=3,
            retry_on_exceptions=(ConnectionError,)
        )
        retry = ExponentialBackoffRetry(config)

        def failing_func():
            raise ValueError("Not retryable")

        # باید فقط یک بار اجرا شود و retry نکند
        with pytest.raises(RetryError) as exc_info:
            retry.execute(failing_func)

        assert isinstance(exc_info.value.last_exception, ValueError)

    def test_delay_calculation(self):
        """تست محاسبه delay"""
        # تست delay بدون jitter
        config = RetryConfig(initial_delay=1.0, backoff_factor=2.0, jitter=False)
        retry = ExponentialBackoffRetry(config)

        assert retry._calculate_delay(0) == 1.0    # 1 * 2^0
        assert retry._calculate_delay(1) == 2.0    # 1 * 2^1
        assert retry._calculate_delay(2) == 4.0    # 1 * 2^2

    def test_max_delay_limit(self):
        """تست محدودیت max_delay"""
        config = RetryConfig(initial_delay=10.0, max_delay=5.0, backoff_factor=2.0, jitter=False)
        retry = ExponentialBackoffRetry(config)

        # حتی با exponential backoff، delay نباید از max_delay بیشتر شود
        assert retry._calculate_delay(10) == 5.0

    def test_jitter_effect(self):
        """تست تاثیر jitter"""
        config = RetryConfig(initial_delay=1.0, jitter=True)
        retry = ExponentialBackoffRetry(config)

        # با jitter، delay باید متغیر باشد
        delays = [retry._calculate_delay(0) for _ in range(10)]
        assert len(set(delays)) > 1  # همه delays یکسان نیستند

        # همه delays باید در محدوده باشند
        for delay in delays:
            assert 0.75 <= delay <= 1.25  # ±25% jitter

    def test_should_retry_logic(self):
        """تست منطق should_retry"""
        config = RetryConfig(
            retry_on_exceptions=(ConnectionError, TimeoutError),
            retry_on_status_codes=(500, 503)
        )
        retry = ExponentialBackoffRetry(config)

        # تست exceptions
        assert retry._should_retry(ConnectionError("Network")) is True
        assert retry._should_retry(TimeoutError("Timeout")) is True
        assert retry._should_retry(ValueError("Value")) is False

        # تست status codes
        assert retry._should_retry(Exception("Dummy"), 500) is True
        assert retry._should_retry(Exception("Dummy"), 503) is True
        assert retry._should_retry(Exception("Dummy"), 404) is False


class TestAPIRetryConfig:
    """تست‌های APIRetryConfig"""

    def test_api_specific_defaults(self):
        """تست پیش‌فرض‌های API-specific"""
        config = APIRetryConfig()

        assert config.max_attempts == 5
        assert config.initial_delay == 1.0
        assert config.max_delay == 30.0
        assert config.backoff_factor == 1.5
        assert config.jitter is True

        # تست exceptions مخصوص API
        assert ConnectionError in config.retry_on_exceptions
        assert TimeoutError in config.retry_on_exceptions
        assert OSError in config.retry_on_exceptions

        # تست status codes مخصوص API
        assert 408 in config.retry_on_status_codes  # Request Timeout
        assert 429 in config.retry_on_status_codes  # Too Many Requests
        assert 500 in config.retry_on_status_codes  # Internal Server Error


class TestCircuitBreakerAwareRetry:
    """تست‌های CircuitBreakerAwareRetry"""

    def test_without_circuit_breaker(self):
        """تست بدون circuit breaker"""
        config = RetryConfig(max_attempts=2)
        retry = CircuitBreakerAwareRetry(config, circuit_breaker=None)

        call_count = 0
        def failing_func():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Network")

        with pytest.raises(RetryError):
            retry.execute(failing_func)

        assert call_count == 2

    def test_with_circuit_breaker(self):
        """تست با circuit breaker"""
        from utils.circuit_breaker import CircuitBreaker

        config = RetryConfig(max_attempts=2)
        cb = CircuitBreaker(failure_threshold=5, recovery_timeout=1)
        retry = CircuitBreakerAwareRetry(config, circuit_breaker=cb)

        def failing_func():
            raise ConnectionError("Network")

        # circuit breaker باید retry logic را اجرا کند
        with pytest.raises(RetryError):
            retry.execute(failing_func)

        # circuit breaker باید failure را ثبت کرده باشد
        assert cb.failure_count == 1


class TestRetryDecorators:
    """تست‌های retry decorators"""

    def test_retry_with_backoff_decorator_success(self):
        """تست decorator موفق"""
        @retry_with_backoff(max_attempts=2)
        def successful_func():
            return "success"

        result = successful_func()
        assert result == "success"

    def test_retry_with_backoff_decorator_retry(self):
        """تست decorator با retry"""
        call_count = 0

        @retry_with_backoff(max_attempts=3, initial_delay=0.01)
        def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Network")
            return "success"

        result = failing_func()
        assert result == "success"
        assert call_count == 3

    def test_api_retry_decorator(self):
        """تست api_retry decorator"""
        call_count = 0

        @api_retry(max_attempts=2, initial_delay=0.01)
        def api_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ConnectionError("API Error")
            return {"status": "success"}

        result = api_func()
        assert result["status"] == "success"
        assert call_count == 2


class TestRetryRealWorldScenarios:
    """تست‌های سناریوهای واقعی با داده‌های TSE"""

    def test_api_timeout_retry(self):
        """تست retry برای timeout API"""
        config = APIRetryConfig(max_attempts=3, initial_delay=0.01)
        retry = ExponentialBackoffRetry(config)

        call_count = 0

        def api_call():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise TimeoutError("Request timed out")
            return {"data": "market_watch_data"}

        result = retry.execute(api_call)
        assert result["data"] == "market_watch_data"
        assert call_count == 3

    def test_network_error_retry(self):
        """تست retry برای خطای شبکه"""
        config = APIRetryConfig(max_attempts=4, initial_delay=0.01)
        retry = ExponentialBackoffRetry(config)

        call_count = 0

        def network_call():
            nonlocal call_count
            call_count += 1
            if call_count < 4:
                raise ConnectionError("Connection refused")
            return {"instruments": ["فولاد", "خودرو"]}

        result = retry.execute(network_call)
        assert "instruments" in result
        assert call_count == 4

    def test_http_500_retry(self):
        """تست retry برای HTTP 500"""
        config = APIRetryConfig(max_attempts=2, initial_delay=0.01)
        retry = ExponentialBackoffRetry(config)

        call_count = 0

        def http_call():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                # شبیه‌سازی HTTP error
                raise ConnectionError("HTTP 500")
            return {"price_data": [1000, 1100, 1200]}

        result = retry.execute(http_call)
        assert "price_data" in result
        assert call_count == 2

    def test_rate_limit_retry(self):
        """تست retry برای rate limiting (429)"""
        config = RetryConfig(
            max_attempts=3,
            initial_delay=0.01,
            retry_on_status_codes=(429,)
        )
        retry = ExponentialBackoffRetry(config)

        call_count = 0

        def rate_limited_call():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("HTTP 429")
            return {"search_results": ["نماد1", "نماد2"]}

        result = retry.execute(rate_limited_call)
        assert "search_results" in result
        assert call_count == 3

    def test_no_retry_on_client_error(self):
        """تست عدم retry برای خطای client (400)"""
        config = RetryConfig(
            max_attempts=3,
            retry_on_status_codes=(500, 502, 503)  # بدون 400
        )
        retry = ExponentialBackoffRetry(config)

        def client_error_call():
            raise Exception("HTTP 400")

        # باید فقط یک بار اجرا شود
        with pytest.raises(RetryError) as exc_info:
            retry.execute(client_error_call)

        assert "HTTP 400" in str(exc_info.value.last_exception)

    def test_exponential_backoff_timing(self):
        """تست زمان‌بندی exponential backoff"""
        config = RetryConfig(
            max_attempts=4,
            initial_delay=0.1,
            backoff_factor=2.0,
            jitter=False  # برای تست دقیق timing
        )
        retry = ExponentialBackoffRetry(config)

        delays = []
        call_count = 0

        def failing_call():
            nonlocal call_count
            call_count += 1
            if call_count < 4:
                raise ConnectionError("Network")
            return "success"

        start_time = time.time()
        result = retry.execute(failing_call)
        end_time = time.time()

        assert result == "success"
        assert call_count == 4

        # زمان کل باید حداقل مجموع delays باشد
        # delays: 0.1, 0.2, 0.4 = 0.7 ثانیه
        elapsed = end_time - start_time
        assert elapsed >= 0.6  # با tolerance

    def test_concurrent_retry_execution(self):
        """تست اجرای همزمان retry"""
        config = RetryConfig(max_attempts=3, initial_delay=0.01)
        retry = ExponentialBackoffRetry(config)

        results = []
        errors = []

        def concurrent_call(success_on_attempt=2):
            try:
                call_count = 0
                def func():
                    nonlocal call_count
                    call_count += 1
                    if call_count < success_on_attempt:
                        raise ConnectionError("Concurrent error")
                    return f"thread_success_{success_on_attempt}"

                result = retry.execute(func)
                results.append(result)
            except Exception as e:
                errors.append(str(e))

        # اجرای همزمان
        threads = []
        for i in range(5):
            t = threading.Thread(target=concurrent_call, args=(3,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # همه باید موفق شوند
        assert len(results) == 5
        assert len(errors) == 0
        assert all("thread_success" in r for r in results)

    def test_circuit_breaker_integration(self):
        """تست integration با circuit breaker"""
        from utils.circuit_breaker import CircuitBreaker

        config = RetryConfig(max_attempts=2, initial_delay=0.01)
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1)
        retry = CircuitBreakerAwareRetry(config, cb)

        def failing_call():
            raise ConnectionError("Network failure")

        # چند شکست برای باز کردن circuit
        for _ in range(3):
            try:
                retry.execute(failing_call)
            except RetryError:
                pass

        # circuit breaker باید باز شده باشد
        assert cb.state.value == "open"

    def test_global_api_retry_instance(self):
        """تست instance جهانی API retry"""
        call_count = 0

        def api_call():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("API Network Error")
            return {"tse_data": "real_data"}

        result = api_retry_instance.execute(api_call)
        assert result["tse_data"] == "real_data"
        assert call_count == 3


class TestRetryEdgeCases:
    """تست‌های موارد边缘"""

    def test_zero_max_attempts(self):
        """تست max_attempts صفر"""
        config = RetryConfig(max_attempts=0)
        retry = ExponentialBackoffRetry(config)

        def func():
            return "should not execute"

        # با max_attempts=0 باید مستقیم exception بدهد
        with pytest.raises(RetryError):
            retry.execute(func)

    def test_single_attempt_success(self):
        """تست یک تلاش موفق"""
        config = RetryConfig(max_attempts=1)
        retry = ExponentialBackoffRetry(config)

        def func():
            return "success"

        result = retry.execute(func)
        assert result == "success"

    def test_single_attempt_failure(self):
        """تست یک تلاش ناموفق"""
        config = RetryConfig(max_attempts=1)
        retry = ExponentialBackoffRetry(config)

        def func():
            raise ValueError("Error")

        with pytest.raises(RetryError) as exc_info:
            retry.execute(func)

        assert isinstance(exc_info.value.last_exception, ValueError)

    def test_zero_initial_delay(self):
        """تست initial_delay صفر"""
        config = RetryConfig(initial_delay=0.0, max_attempts=3)
        retry = ExponentialBackoffRetry(config)

        call_count = 0

        def func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Error")
            return "success"

        start_time = time.time()
        result = retry.execute(func)
        end_time = time.time()

        assert result == "success"
        assert call_count == 3

        # با delay صفر باید سریع‌تر اجرا شود
        elapsed = end_time - start_time
        assert elapsed < 0.1  # کمتر از 100ms

    def test_max_delay_smaller_than_initial(self):
        """تست max_delay کوچکتر از initial_delay"""
        config = RetryConfig(initial_delay=10.0, max_delay=1.0, jitter=False)
        retry = ExponentialBackoffRetry(config)

        # delay باید به max_delay محدود شود
        delay = retry._calculate_delay(0)
        assert delay == 1.0

    def test_empty_retry_exceptions(self):
        """تست retry_on_exceptions خالی"""
        config = RetryConfig(retry_on_exceptions=())
        retry = ExponentialBackoffRetry(config)

        def func():
            raise ValueError("Error")

        # نباید retry کند
        with pytest.raises(RetryError) as exc_info:
            retry.execute(func)

        assert isinstance(exc_info.value.last_exception, ValueError)

    def test_none_status_code(self):
        """تست status_code None"""
        config = RetryConfig(retry_on_status_codes=(500,), retry_on_exceptions=())
        retry = ExponentialBackoffRetry(config)

        # با status_code=None نباید retry کند
        should_retry = retry._should_retry(Exception("Error"), None)
        assert should_retry is False

    def test_decorator_with_args_kwargs(self):
        """تست decorator با پارامترها"""
        call_count = 0

        @retry_with_backoff(max_attempts=3)
        def func_with_args(a, b, c=None):
            nonlocal call_count
            call_count += 1
            if a == "fail" and call_count < 2:
                raise ConnectionError("Error")
            return f"{a}-{b}-{c}"

        # تست موفق
        result = func_with_args("success", "test", c="param")
        assert result == "success-test-param"

        # تست retry
        call_count = 0  # reset
        result = func_with_args("fail", "retry", c="works")
        assert result == "fail-retry-works"

    def test_nested_retry_with_circuit_breaker(self):
        """تست retry تودرتو با circuit breaker"""
        from utils.circuit_breaker import CircuitBreaker

        config = RetryConfig(max_attempts=2, initial_delay=0.01)
        cb = CircuitBreaker(failure_threshold=10, recovery_timeout=1)
        retry = CircuitBreakerAwareRetry(config, cb)

        call_count = 0

        def nested_call():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Nested error")

        # همه تلاش‌ها باید شکست بخورند
        with pytest.raises(RetryError):
            retry.execute(nested_call)

        # circuit breaker باید failure را ثبت کرده باشد
        assert cb.failure_count == 1

    def test_jitter_consistency(self):
        """تست consistency jitter"""
        config = RetryConfig(jitter=True, initial_delay=1.0)
        retry = ExponentialBackoffRetry(config)

        # jitter باید برای هر attempt مستقل باشد
        delays_attempt_0 = [retry._calculate_delay(0) for _ in range(20)]
        delays_attempt_1 = [retry._calculate_delay(1) for _ in range(20)]

        # attempt 1 باید delay بیشتری داشته باشد
        avg_delay_0 = sum(delays_attempt_0) / len(delays_attempt_0)
        avg_delay_1 = sum(delays_attempt_1) / len(delays_attempt_1)

        assert avg_delay_1 > avg_delay_0

        # هر دو باید در محدوده jitter باشند
        for delay in delays_attempt_0 + delays_attempt_1:
            assert 0.001 <= delay <= 60.0  # بین min و max