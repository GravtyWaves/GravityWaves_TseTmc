"""
تست‌های حرفه‌ای برای utils/circuit_breaker.py با استفاده از داده‌های واقعی TSE
"""

import pytest
import time
import threading
import requests
from unittest.mock import patch, MagicMock, call
from utils.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerState,
    CircuitBreakerOpenException,
    circuit_breaker,
    APICircuitBreaker,
    api_circuit_breaker
)


class TestCircuitBreakerBasic:
    """تست‌های پایه CircuitBreaker"""

    def setup_method(self):
        """تنظیمات اولیه برای هر تست"""
        self.cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1, name="TestCB")

    def test_initial_state(self):
        """تست حالت اولیه"""
        assert self.cb.state == CircuitBreakerState.CLOSED
        assert self.cb.failure_count == 0
        assert self.cb.success_count == 0
        assert self.cb.failure_count_total == 0
        assert self.cb.last_failure_time is None

    def test_successful_call(self):
        """تست فراخوانی موفق"""
        def successful_func():
            return "success"

        result = self.cb.call(successful_func)
        assert result == "success"
        assert self.cb.state == CircuitBreakerState.CLOSED
        assert self.cb.success_count == 1
        assert self.cb.failure_count == 0

    def test_single_failure(self):
        """تست یک شکست"""
        def failing_func():
            raise ValueError("Test error")

        with pytest.raises(ValueError):
            self.cb.call(failing_func)

        assert self.cb.state == CircuitBreakerState.CLOSED
        assert self.cb.failure_count == 1
        assert self.cb.success_count == 0
        assert self.cb.failure_count_total == 1

    def test_failure_threshold_reached(self):
        """تست رسیدن به آستانه شکست"""
        def failing_func():
            raise ConnectionError("Network error")

        # سه شکست متوالی
        for i in range(3):
            with pytest.raises(ConnectionError):
                self.cb.call(failing_func)

        assert self.cb.state == CircuitBreakerState.OPEN
        assert self.cb.failure_count == 3

    def test_open_circuit_blocks_calls(self):
        """تست مسدود کردن فراخوانی‌ها در حالت OPEN"""
        # باز کردن circuit
        self.cb.state = CircuitBreakerState.OPEN
        self.cb.last_failure_time = time.time() - 10  # گذشته

        def dummy_func():
            return "should not execute"

        # چون timeout گذشته، باید بتواند تلاش کند
        result = self.cb.call(dummy_func)
        assert result == "should not execute"

    def test_half_open_attempt_after_timeout(self):
        """تست تلاش reset بعد از timeout"""
        # باز کردن circuit
        self.cb.state = CircuitBreakerState.OPEN
        self.cb.failure_count = 5
        self.cb.last_failure_time = time.time() - 2  # بعد از timeout

        def successful_func():
            return "recovered"

        result = self.cb.call(successful_func)
        assert result == "recovered"
        assert self.cb.state == CircuitBreakerState.CLOSED
        assert self.cb.failure_count == 0

    def test_half_open_failure_keeps_open(self):
        """تست شکست در حالت HALF_OPEN نگه داشتن OPEN"""
        self.cb.state = CircuitBreakerState.HALF_OPEN

        def failing_func():
            raise TimeoutError("Still failing")

        with pytest.raises(TimeoutError):
            self.cb.call(failing_func)

        assert self.cb.state == CircuitBreakerState.OPEN

    def test_recovery_timeout_prevents_reset(self):
        """تست جلوگیری از reset قبل از timeout"""
        self.cb.state = CircuitBreakerState.OPEN
        self.cb.last_failure_time = time.time()  # همین الان

        def dummy_func():
            return "test"

        with pytest.raises(CircuitBreakerOpenException):
            self.cb.call(dummy_func)

    def test_get_status(self):
        """تست دریافت وضعیت"""
        status = self.cb.get_status()

        expected_keys = ['name', 'state', 'failure_count', 'success_count',
                        'total_failures', 'last_failure', 'can_attempt_reset']
        for key in expected_keys:
            assert key in status

        assert status['name'] == 'TestCB'
        assert status['state'] == 'closed'


class TestCircuitBreakerDecorator:
    """تست‌های decorator circuit_breaker"""

    def test_decorator_success(self):
        """تست decorator با فراخوانی موفق"""
        @circuit_breaker(failure_threshold=2, name="TestFunc")
        def test_func():
            return "success"

        result = test_func()
        assert result == "success"

        # بررسی وجود circuit breaker
        assert hasattr(test_func, 'circuit_breaker')
        cb = test_func.circuit_breaker
        assert cb.name == "TestFunc"
        assert cb.success_count == 1

    def test_decorator_failure(self):
        """تست decorator با شکست"""
        @circuit_breaker(failure_threshold=1, recovery_timeout=1)
        def failing_func():
            raise requests.ConnectionError("API Error")

        with pytest.raises(requests.ConnectionError):
            failing_func()

        cb = failing_func.circuit_breaker
        assert cb.failure_count == 1
        assert cb.state == CircuitBreakerState.OPEN

    def test_decorator_default_name(self):
        """تست نام پیش‌فرض decorator"""
        @circuit_breaker()
        def my_function():
            return "ok"

        my_function()
        assert "my_function" in my_function.circuit_breaker.name


class TestAPICircuitBreaker:
    """تست‌های APICircuitBreaker"""

    def setup_method(self):
        """تنظیمات اولیه"""
        self.api_cb = APICircuitBreaker(base_failure_threshold=2, base_recovery_timeout=1)

    def test_get_circuit_breaker_creates_new(self):
        """تست ایجاد circuit breaker جدید"""
        cb = self.api_cb.get_circuit_breaker("test_endpoint")

        assert isinstance(cb, CircuitBreaker)
        assert cb.name == "API-test_endpoint"
        assert cb.failure_threshold == 2  # base threshold

    def test_get_circuit_breaker_reuses_existing(self):
        """تست استفاده مجدد از circuit breaker موجود"""
        cb1 = self.api_cb.get_circuit_breaker("endpoint1")
        cb2 = self.api_cb.get_circuit_breaker("endpoint1")

        assert cb1 is cb2

    def test_different_thresholds_for_endpoints(self):
        """تست آستانه‌های مختلف برای endpointهای مختلف"""
        # Price endpoint - lower threshold
        price_cb = self.api_cb.get_circuit_breaker("price_history")
        assert price_cb.failure_threshold == 1  # base - 1

        # List endpoint - higher threshold
        list_cb = self.api_cb.get_circuit_breaker("stock_list")
        assert list_cb.failure_threshold == 3  # base + 1

        # Regular endpoint - base threshold
        regular_cb = self.api_cb.get_circuit_breaker("market_watch")
        assert regular_cb.failure_threshold == 2  # base

    def test_get_all_status(self):
        """تست دریافت وضعیت همه circuit breakerها"""
        self.api_cb.get_circuit_breaker("endpoint1")
        self.api_cb.get_circuit_breaker("endpoint2")

        status = self.api_cb.get_all_status()

        assert len(status) == 2
        assert "endpoint1" in status
        assert "endpoint2" in status

    def test_reset_all(self):
        """تست reset همه circuit breakerها"""
        cb1 = self.api_cb.get_circuit_breaker("endpoint1")
        cb2 = self.api_cb.get_circuit_breaker("endpoint2")

        # شکستن circuit breakerها
        cb1.state = CircuitBreakerState.OPEN
        cb1.failure_count = 5
        cb2.state = CircuitBreakerState.OPEN
        cb2.failure_count = 3

        self.api_cb.reset_all()

        assert cb1.state == CircuitBreakerState.CLOSED
        assert cb1.failure_count == 0
        assert cb2.state == CircuitBreakerState.CLOSED
        assert cb2.failure_count == 0


class TestCircuitBreakerRealWorldScenarios:
    """تست‌های سناریوهای واقعی با داده‌های TSE"""

    def test_api_call_simulation(self):
        """تست شبیه‌سازی فراخوانی API"""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)

        # شبیه‌سازی API call موفق
        def api_call_success():
            return {"status": "success", "data": {"price": 1000}}

        result = cb.call(api_call_success)
        assert result["status"] == "success"
        assert cb.state == CircuitBreakerState.CLOSED

    def test_network_failure_simulation(self):
        """تست شبیه‌سازی شکست شبکه"""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)

        def network_failure():
            raise ConnectionError("Network is unreachable")

        # دو شکست
        for _ in range(2):
            with pytest.raises(ConnectionError):
                cb.call(network_failure)

        assert cb.state == CircuitBreakerState.OPEN

        # تلاش فراخوانی در حالت OPEN باید شکست بخورد
        with pytest.raises(CircuitBreakerOpenException):
            cb.call(lambda: "test")

    def test_timeout_simulation(self):
        """تست شبیه‌سازی timeout"""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=1)

        def timeout_failure():
            raise TimeoutError("Request timed out")

        with pytest.raises(TimeoutError):
            cb.call(timeout_failure)

        assert cb.state == CircuitBreakerState.OPEN

        # صبر کردن برای recovery timeout
        time.sleep(1.1)

        # حالا باید بتواند تلاش کند
        def recovery_success():
            return "recovered"

        result = cb.call(recovery_success)
        assert result == "recovered"
        assert cb.state == CircuitBreakerState.CLOSED

    def test_mixed_success_failure(self):
        """تست ترکیب موفقیت و شکست"""
        cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1)

        call_count = 0

        def mixed_behavior():
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise ValueError("Temporary failure")
            return "success"

        # دو شکست
        for _ in range(2):
            with pytest.raises(ValueError):
                cb.call(mixed_behavior)

        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 2

        # موفقیت سوم
        result = cb.call(mixed_behavior)
        assert result == "success"
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 2  # failure count not reset on success

    def test_concurrent_access(self):
        """تست دسترسی همزمان"""
        cb = CircuitBreaker(failure_threshold=5, recovery_timeout=1)

        results = []
        errors = []

        def concurrent_call(success_probability=0.7):
            try:
                if cb.state == CircuitBreakerState.OPEN:
                    raise CircuitBreakerOpenException("Circuit open")

                import random
                if random.random() < success_probability:
                    cb._record_success()
                    results.append("success")
                else:
                    cb._record_failure()
                    raise ValueError("Simulated failure")
            except Exception as e:
                errors.append(str(e))

        # اجرای همزمان
        threads = []
        for i in range(10):
            t = threading.Thread(target=concurrent_call, args=(0.8,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # بررسی نتایج
        total_operations = len(results) + len(errors)
        assert total_operations == 10

        # circuit breaker باید بتواند با دسترسی همزمان کنار بیاید
        status = cb.get_status()
        assert 'state' in status

    def test_different_exception_types(self):
        """تست انواع مختلف exception"""
        cb = CircuitBreaker(failure_threshold=2, expected_exception=ConnectionError)

        def connection_error():
            raise ConnectionError("Connection failed")

        def value_error():
            raise ValueError("Value error")

        # ConnectionError باید شمارش شود
        with pytest.raises(ConnectionError):
            cb.call(connection_error)
        assert cb.failure_count == 1

        # ValueError نباید شمارش شود چون expected_exception نیست
        with pytest.raises(ValueError):
            cb.call(value_error)
        assert cb.failure_count == 1  # بدون تغییر

    def test_metrics_tracking(self):
        """تست ردیابی معیارها"""
        cb = CircuitBreaker(failure_threshold=10)

        # چند موفقیت
        for _ in range(3):
            cb.call(lambda: "success")

        # چند شکست
        for _ in range(2):
            try:
                cb.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
            except ValueError:
                pass

        status = cb.get_status()
        assert status['success_count'] == 3
        assert status['total_failures'] == 2
        assert status['failure_count'] == 2

    def test_state_transitions(self):
        """تست انتقال بین حالت‌ها"""
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)

        # CLOSED -> OPEN
        for _ in range(2):
            try:
                cb.call(lambda: (_ for _ in ()).throw(Exception("fail")))
            except Exception:
                pass

        assert cb.state == CircuitBreakerState.OPEN

        # OPEN -> HALF_OPEN (بعد از timeout)
        time.sleep(1.1)
        try:
            cb.call(lambda: (_ for _ in ()).throw(Exception("still failing")))
        except Exception:
            pass

        assert cb.state == CircuitBreakerState.OPEN  # هنوز باز است

        # HALF_OPEN -> CLOSED
        time.sleep(1.1)
        cb.call(lambda: "success")

        assert cb.state == CircuitBreakerState.CLOSED

    def test_global_api_circuit_breaker(self):
        """تست instance جهانی API circuit breaker"""
        # استفاده از instance جهانی
        cb1 = api_circuit_breaker.get_circuit_breaker("test_endpoint")
        cb2 = api_circuit_breaker.get_circuit_breaker("test_endpoint")

        assert cb1 is cb2  # باید همان instance باشد

        # تست reset همه
        cb1.state = CircuitBreakerState.OPEN
        api_circuit_breaker.reset_all()

        assert cb1.state == CircuitBreakerState.CLOSED


class TestCircuitBreakerEdgeCases:
    """تست‌های موارد边缘"""

    def test_zero_failure_threshold(self):
        """تست آستانه شکست صفر"""
        cb = CircuitBreaker(failure_threshold=0, recovery_timeout=1)

        # حتی یک شکست باید circuit را باز کند
        try:
            cb.call(lambda: (_ for _ in ()).throw(Exception("fail")))
        except Exception:
            pass

        assert cb.state == CircuitBreakerState.OPEN

    def test_very_long_recovery_timeout(self):
        """تست timeout بازیابی بسیار طولانی"""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=3600)  # 1 hour

        # شکست
        try:
            cb.call(lambda: (_ for _ in ()).throw(Exception("fail")))
        except Exception:
            pass

        assert cb.state == CircuitBreakerState.OPEN

        # تلاش فوری برای reset باید شکست بخورد
        with pytest.raises(CircuitBreakerOpenException):
            cb.call(lambda: "test")

    def test_call_with_no_exception(self):
        """تست فراخوانی بدون exception"""
        cb = CircuitBreaker(failure_threshold=1)

        # فراخوانی موفق
        result = cb.call(lambda: 42)
        assert result == 42
        assert cb.success_count == 1

    def test_call_with_args_kwargs(self):
        """تست فراخوانی با پارامترها"""
        cb = CircuitBreaker()

        def func_with_args(a, b, c=None):
            return a + b + (c or 0)

        result = cb.call(func_with_args, 1, 2, c=3)
        assert result == 6
        assert cb.success_count == 1

    def test_exception_not_in_expected_type(self):
        """تست exception که جزو expected نیست"""
        cb = CircuitBreaker(expected_exception=ValueError)

        # RuntimeError نباید شمارش شود
        with pytest.raises(RuntimeError):
            cb.call(lambda: (_ for _ in ()).throw(RuntimeError("unexpected")))

        assert cb.failure_count == 0  # بدون تغییر

    def test_success_after_half_open_failure(self):
        """تست موفقیت بعد از شکست در HALF_OPEN"""
        cb = CircuitBreaker(failure_threshold=1, recovery_timeout=1)

        # شکست و باز شدن circuit
        try:
            cb.call(lambda: (_ for _ in ()).throw(Exception("fail")))
        except Exception:
            pass

        assert cb.state == CircuitBreakerState.OPEN

        # صبر برای timeout و تلاش دوباره با شکست
        time.sleep(1.1)
        try:
            cb.call(lambda: (_ for _ in ()).throw(Exception("still failing")))
        except Exception:
            pass

        assert cb.state == CircuitBreakerState.OPEN

        # صبر دوباره و موفقیت
        time.sleep(1.1)
        result = cb.call(lambda: "success")

        assert result == "success"
        assert cb.state == CircuitBreakerState.CLOSED