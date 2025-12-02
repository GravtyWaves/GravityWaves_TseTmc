"""
تست‌های حرفه‌ای برای utils/rate_limiter.py با استفاده از داده‌های واقعی TSE
"""

import pytest
import time
import threading
from unittest.mock import patch, MagicMock
from utils.rate_limiter import (
    RateLimiter,
    SlidingWindowRateLimiter,
    APIRateLimiter,
    RateLimitExceeded,
    rate_limit,
    api_rate_limiter
)


class TestRateLimiterBasic:
    """تست‌های پایه RateLimiter"""

    def setup_method(self):
        """تنظیمات اولیه برای هر تست"""
        self.limiter = RateLimiter(rate=10, capacity=20)  # 10 tokens/second, capacity 20

    def test_initial_state(self):
        """تست حالت اولیه"""
        assert self.limiter.rate == 10
        assert self.limiter.capacity == 20
        assert self.limiter.tokens == 20  # شروع با capacity کامل

    def test_acquire_single_token(self):
        """تست دریافت یک token"""
        assert self.limiter.acquire(1) is True
        assert self.limiter.tokens == 19

    def test_acquire_multiple_tokens(self):
        """تست دریافت چند token"""
        assert self.limiter.acquire(5) is True
        assert self.limiter.tokens == 15

    def test_acquire_insufficient_tokens(self):
        """تست دریافت tokens ناکافی"""
        # خالی کردن bucket
        self.limiter.tokens = 3
        assert self.limiter.acquire(5) is False
        assert self.limiter.tokens == pytest.approx(3, abs=0.05)  # بدون تغییر

    def test_token_refill(self):
        """تست refill tokens"""
        # خالی کردن bucket
        self.limiter.tokens = 0
        self.limiter.last_update = time.time() - 1  # 1 ثانیه قبل

        # refill باید 10 tokens اضافه کند (rate * elapsed)
        self.limiter._refill_tokens()
        assert self.limiter.tokens == 10

    def test_wait_for_tokens(self):
        import time
        """تست انتظار برای tokens"""
        # خالی کردن bucket
        self.limiter.tokens = 0

        start_time = time.time()
        wait_time = self.limiter.wait_for_tokens(5)
        end_time = time.time()

        assert wait_time > 0
        assert end_time - start_time >= wait_time

    def test_burst_capacity(self):
        """تست ظرفیت burst"""
        # دریافت همه tokens به یکباره
        assert self.limiter.acquire(20) is True
        assert self.limiter.tokens == 0

        # تلاش برای دریافت بیشتر باید شکست بخورد
        assert self.limiter.acquire(1) is False


class TestSlidingWindowRateLimiter:
    """تست‌های SlidingWindowRateLimiter"""

    def setup_method(self):
        """تنظیمات اولیه"""
        self.limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=1)

    def test_initial_state(self):
        """تست حالت اولیه"""
        assert self.limiter.max_requests == 5
        assert self.limiter.window_seconds == 1
        assert len(self.limiter.requests) == 0

    def test_acquire_within_limit(self):
        """تست دریافت permission در محدوده"""
        for i in range(5):
            assert self.limiter.acquire() is True
            assert len(self.limiter.requests) == i + 1

    def test_acquire_over_limit(self):
        """تست دریافت permission بیش از حد"""
        # پر کردن پنجره
        for _ in range(5):
            self.limiter.acquire()

        # درخواست ششم باید رد شود
        assert self.limiter.acquire() is False
        assert len(self.limiter.requests) == 5

    def test_window_expiration(self):
        """تست انقضای پنجره"""
        # پر کردن پنجره
        for _ in range(5):
            self.limiter.acquire()

        # منتظر ماندن تا پنجره expire شود
        time.sleep(1.1)

        # حالا باید بتواند درخواست جدید بدهد
        assert self.limiter.acquire() is True
        assert len(self.limiter.requests) == 1  # قدیمی‌ها پاک شده‌اند

    def test_wait_for_slot(self):
        """تست انتظار برای slot"""
        # پر کردن پنجره
        for _ in range(5):
            self.limiter.acquire()

        start_time = time.time()
        wait_time = self.limiter.wait_for_slot()
        end_time = time.time()

        assert wait_time > 0
        assert end_time - start_time >= 1  # حداقل 1 ثانیه انتظار
        assert len(self.limiter.requests) == 1  # یک درخواست جدید اضافه شده


class TestAPIRateLimiter:
    """تست‌های APIRateLimiter"""

    def setup_method(self):
        """تنظیمات اولیه"""
        self.api_limiter = APIRateLimiter()

    def test_get_limiter_creates_new(self):
        """تست ایجاد limiter جدید"""
        limiter = self.api_limiter.get_limiter("test_endpoint")

        assert isinstance(limiter, RateLimiter)
        assert limiter in self.api_limiter.limiters.values()

    def test_get_limiter_reuses_existing(self):
        """تست استفاده مجدد از limiter موجود"""
        limiter1 = self.api_limiter.get_limiter("endpoint1")
        limiter2 = self.api_limiter.get_limiter("endpoint1")

        assert limiter1 is limiter2

    def test_endpoint_type_detection(self):
        """تست تشخیص نوع endpoint"""
        # Search endpoint
        search_limiter = self.api_limiter.get_limiter("instrument_search")
        assert search_limiter.rate == 10  # search rate

        # History endpoint
        history_limiter = self.api_limiter.get_limiter("price_history")
        assert history_limiter.rate == 2  # history rate

        # Details endpoint
        details_limiter = self.api_limiter.get_limiter("stock_details")
        assert details_limiter.rate == 20  # details rate

        # Default endpoint
        default_limiter = self.api_limiter.get_limiter("unknown_endpoint")
        assert default_limiter.rate == 10  # default rate

    def test_acquire_endpoint_permission(self):
        """تست دریافت permission برای endpoint"""
        # تست endpoint با محدودیت بالا
        assert self.api_limiter.acquire("stock_details", 1) is True

        # تست endpoint با محدودیت پایین
        history_limiter = self.api_limiter.get_limiter("price_history")
        # خالی کردن tokens
        history_limiter.tokens = 0

        assert self.api_limiter.acquire("price_history", 1) is False

    def test_wait_for_slot_endpoint(self):
        """تست انتظار برای slot در endpoint"""
        # خالی کردن tokens برای history endpoint
        history_limiter = self.api_limiter.get_limiter("price_history")
        history_limiter.tokens = 0

        start_time = time.time()
        wait_time = self.api_limiter.wait_for_slot("price_history", 1)
        end_time = time.time()

        assert wait_time > 0
        assert end_time - start_time >= wait_time

    def test_get_status(self):
        """تست دریافت وضعیت"""
        self.api_limiter.get_limiter("endpoint1")
        self.api_limiter.get_limiter("endpoint2")

        status = self.api_limiter.get_status()

        assert len(status) == 2
        assert "endpoint1" in status
        assert "endpoint2" in status

        # بررسی ساختار status
        for endpoint_status in status.values():
            required_keys = ['tokens', 'capacity', 'rate', 'last_update']
            for key in required_keys:
                assert key in endpoint_status


class TestRateLimitDecorator:
    """تست‌های decorator rate_limit"""

    def test_decorator_without_wait(self):
        """تست decorator بدون انتظار"""
        call_count = 0

        @rate_limit(rate=10, capacity=2, wait=False)
        def limited_func():
            nonlocal call_count
            call_count += 1
            return f"call_{call_count}"

        # دو فراخوانی موفق
        assert limited_func() == "call_1"
        assert limited_func() == "call_2"

        # سومین فراخوانی باید rate limit بخورد
        with pytest.raises(RateLimitExceeded):
            limited_func()

    def test_decorator_with_wait(self):
        """تست decorator با انتظار"""
        call_count = 0

        @rate_limit(rate=10, capacity=1, wait=True)
        def limited_func():
            nonlocal call_count
            call_count += 1
            return f"call_{call_count}"

        start_time = time.time()

        # سه فراخوانی - دو تای آخر باید صبر کنند
        result1 = limited_func()
        result2 = limited_func()
        result3 = limited_func()

        end_time = time.time()

        assert result1 == "call_1"
        assert result2 == "call_2"
        assert result3 == "call_3"
        assert end_time - start_time >= 0.1  # حداقل کمی انتظار

    def test_decorator_function_name(self):
        """تست نام تابع در decorator"""
        @rate_limit(rate=5, capacity=5, wait=False)
        def my_test_function():
            return "ok"

        # بررسی اینکه decorator تابع اصلی را حفظ کرده
        assert my_test_function.__name__ == "my_test_function"


class TestRateLimiterRealWorldScenarios:
    """تست‌های سناریوهای واقعی با داده‌های TSE"""

    def test_api_burst_handling(self):
        """تست مدیریت burst در API calls"""
        limiter = RateLimiter(rate=5, capacity=10)  # 5/sec, burst 10

        # burst اولیه
        success_count = 0
        for _ in range(10):
            if limiter.acquire():
                success_count += 1

        assert success_count == 10
        assert limiter.tokens == 0

        # صبر برای refill
        time.sleep(1.1)

        # حالا باید tokens refill شده باشند
        limiter._refill_tokens()
        assert limiter.tokens >= 5  # حداقل 5 tokens اضافه شده

    def test_sliding_window_realistic_load(self):
        """تست بار واقعی در sliding window"""
        limiter = SlidingWindowRateLimiter(max_requests=100, window_seconds=60)  # 100 requests/minute

        # شبیه‌سازی ترافیک عادی
        success_count = 0
        for _ in range(100):
            if limiter.acquire():
                success_count += 1
            time.sleep(0.01)  # 10ms delay بین requests

        assert success_count == 100

        # درخواست 101 باید رد شود
        assert limiter.acquire() is False

    def test_concurrent_token_acquisition(self):
        """تست دریافت همزمان tokens"""
        limiter = RateLimiter(rate=100, capacity=1000)

        results = []
        errors = []

        def concurrent_acquire():
            try:
                success = limiter.acquire(10)
                results.append(success)
            except Exception as e:
                errors.append(str(e))

        # ایجاد threads همزمان
        threads = []
        for i in range(10):
            t = threading.Thread(target=concurrent_acquire)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # همه باید موفق شوند (capacity کافی)
        assert len(results) == 10
        assert all(results)
        assert len(errors) == 0

        # مجموع tokens مصرف شده باید 100 باشد
        assert limiter.tokens == pytest.approx(900, abs=1)

    def test_api_endpoint_rate_limiting(self):
        """تست rate limiting برای endpointهای مختلف API"""
        # تست endpointهای مختلف TSE
        endpoints = [
            "instrument_search",  # search type
            "price_history",     # history type
            "stock_details",     # details type
            "market_watch"       # default type
        ]

        for endpoint in endpoints:
            # چند درخواست متوالی
            for i in range(3):
                allowed = api_rate_limiter.acquire(endpoint)
                if i < 2:  # دو تای اول باید موفق شوند
                    assert allowed, f"Request {i+1} to {endpoint} should be allowed"
                # سومین ممکن است بسته به محدودیت رد شود

    def test_rate_limiter_recovery(self):
        """تست بازیابی rate limiter"""
        limiter = RateLimiter(rate=1, capacity=5)  # 1 token/second

        # مصرف همه tokens
        for _ in range(5):
            assert limiter.acquire() is True

        assert limiter.tokens == 0

        # انتظار برای refill کامل
        time.sleep(5.1)

        # refill
        limiter._refill_tokens()

        # باید دوباره capacity کامل داشته باشد
        assert limiter.tokens >= 4.9  # حدود 5 tokens

    def test_sliding_window_edge_cases(self):
        """تست موارد边缘 sliding window"""
        limiter = SlidingWindowRateLimiter(max_requests=1, window_seconds=1)

        # یک درخواست موفق
        assert limiter.acquire() is True

        # درخواست دوم باید رد شود
        assert limiter.acquire() is False

        # صبر دقیق 1 ثانیه
        time.sleep(1.0)

        # حالا باید بتواند درخواست بدهد
        assert limiter.acquire() is True

    def test_token_bucket_precision(self):
        """تست دقت token bucket"""
        limiter = RateLimiter(rate=0.5, capacity=10)  # 0.5 tokens/second

        # مصرف tokens
        limiter.acquire(5)
        initial_tokens = limiter.tokens

        # صبر 2 ثانیه
        time.sleep(2.0)

        # refill باید 1 token اضافه کند (0.5 * 2)
        limiter._refill_tokens()

        # tokens باید افزایش یافته باشد
        assert limiter.tokens > initial_tokens

    def test_global_api_rate_limiter(self):
        """تست global API rate limiter"""
        # استفاده از instance جهانی
        limiter1 = api_rate_limiter.get_limiter("global_test")
        limiter2 = api_rate_limiter.get_limiter("global_test")

        assert limiter1 is limiter2

        # تست thread safety
        def global_test():
            return api_rate_limiter.acquire("global_test")

        threads = []
        results = []

        for _ in range(5):
            t = threading.Thread(target=lambda: results.append(global_test()))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # همه باید موفق شوند یا rate limit بخورند
        assert len(results) == 5
        assert all(isinstance(r, bool) for r in results)


class TestRateLimiterEdgeCases:
    """تست‌های موارد边缘"""

    def test_zero_rate(self):
        """تست rate صفر"""
        limiter = RateLimiter(rate=0, capacity=10)

        # باید بتواند از capacity اولیه استفاده کند
        assert limiter.acquire(5) is True
        assert limiter.tokens == 5

        # refill نباید چیزی اضافه کند
        time.sleep(1)
        limiter._refill_tokens()
        assert limiter.tokens == 5

    def test_very_high_rate(self):
        """تست rate بسیار بالا"""
        limiter = RateLimiter(rate=1000, capacity=100)

        # باید خیلی سریع refill شود
        limiter.tokens = 0
        limiter.last_update = time.time() - 1

        limiter._refill_tokens()
        assert limiter.tokens >= 100  # capacity

    def test_negative_tokens_request(self):
        """تست درخواست tokens منفی"""
        limiter = RateLimiter(rate=10, capacity=20)

        # درخواست tokens منفی باید False برگرداند
        assert limiter.acquire(-1) is False
        assert limiter.tokens == 20  # بدون تغییر

    def test_zero_capacity(self):
        """تست capacity صفر"""
        limiter = RateLimiter(rate=10, capacity=0)

        assert limiter.acquire(1) is False
        assert limiter.tokens == 0

    def test_sliding_window_zero_window(self):
        """تست sliding window با window صفر"""
        limiter = SlidingWindowRateLimiter(max_requests=5, window_seconds=0)

        # با window صفر، هیچ وقت expire نمی‌شود
        for _ in range(5):
            assert limiter.acquire() is True

        assert limiter.acquire() is False  # همیشه رد می‌شود

    def test_sliding_window_zero_requests(self):
        """تست sliding window با max_requests صفر"""
        limiter = SlidingWindowRateLimiter(max_requests=0, window_seconds=1)

        # هیچ وقت اجازه نمی‌دهد
        assert limiter.acquire() is False

    def test_decorator_with_zero_rate(self):
        """تست decorator با rate صفر"""
        @rate_limit(rate=0, capacity=1, wait=False)
        def func():
            return "ok"

        # یک بار موفق
        assert func() == "ok"

        # دومین بار rate limit
        with pytest.raises(RateLimitExceeded):
            func()

    def test_wait_for_tokens_with_zero_rate(self):
        """تست wait_for_tokens با rate صفر"""
        limiter = RateLimiter(rate=0, capacity=5)

        # خالی کردن bucket
        limiter.tokens = 0

        # باید برای همیشه صبر کند - تست با timeout
        with patch('time.sleep') as mock_sleep:
            # شبیه‌سازی timeout بعد از چند تلاش
            mock_sleep.side_effect = KeyboardInterrupt()

            with pytest.raises(KeyboardInterrupt):
                limiter.wait_for_tokens(1)

    def test_concurrent_sliding_window(self):
        """تست concurrent access به sliding window"""
        limiter = SlidingWindowRateLimiter(max_requests=10, window_seconds=1)

        results = []

        def concurrent_request():
            result = limiter.acquire()
            results.append(result)

        threads = []
        for _ in range(15):  # بیش از حد مجاز
            t = threading.Thread(target=concurrent_request)
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # دقیقاً 10 تای اول باید موفق شوند
        success_count = sum(results)
        assert success_count == 10
        assert len(results) == 15