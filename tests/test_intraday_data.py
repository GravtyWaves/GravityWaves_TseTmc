"""
تست‌های حرفه‌ای برای api/intraday_data.py با استفاده از داده‌های واقعی TSE
"""

import pytest
import pandas as pd
import jdatetime
from unittest.mock import patch, MagicMock
from api.intraday_data import (
    get_intraday_trades_scraping,
    get_order_book_scraping,
    get_real_time_price_scraping,
    get_trade_summary_scraping
)


class TestIntradayDataIntegration:
    """تست‌های یکپارچه برای Intraday Data با داده‌های واقعی"""

    def setup_method(self):
        """تنظیمات اولیه برای هر تست"""
        # نمادهای واقعی TSE برای تست
        self.test_symbols = {
            'web_id': '65883838195688438',  # نماد نمونه
            'symbol': 'فولاد'  # نماد نمونه
        }

    @pytest.mark.slow
    @patch('requests.get')
    def test_get_intraday_trades_real_data(self, mock_get):
        """تست دریافت معاملات لحظه‌ای با داده‌های واقعی (mocked)"""
        # Mock response for intraday trades
        mock_response = MagicMock()
        mock_response.text = (
            '08:30:00,1000,10,10000,123,456;08:31:00,1010,5,5050,124,457'
        )
        mock_get.return_value = mock_response
        df = get_intraday_trades_scraping(self.test_symbols['web_id'])
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        expected_columns = ['time', 'price', 'volume', 'value', 'buyer_id', 'seller_id']
        for col in expected_columns:
            assert col in df.columns
        assert (df['price'] > 0).all()
        assert (df['volume'] > 0).all()
        assert (df['value'] > 0).all()

    @pytest.mark.slow
    @patch('requests.get')
    def test_get_intraday_trades_with_date(self, mock_get):
        """تست دریافت معاملات با تاریخ مشخص (mocked)"""
        today = jdatetime.date.today().strftime('%Y%m%d')
        mock_response = MagicMock()
        mock_response.text = (
            '08:30:00,1000,10,10000,123,456;08:31:00,1010,5,5050,124,457'
        )
        mock_get.return_value = mock_response
        df = get_intraday_trades_scraping(self.test_symbols['web_id'], today)
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        print(f"Trades for {today}: {len(df)} records")

    @pytest.mark.slow
    @patch('requests.get')
    def test_get_order_book_real_data(self, mock_get):
        """تست دریافت Order Book با داده‌های واقعی (mocked)"""
        mock_response = MagicMock()
        mock_response.text = (
            '65883838195688438,1,10,20,1000,1010,100,200'
        )
        mock_get.return_value = mock_response
        order_book = get_order_book_scraping(self.test_symbols['web_id'])
        assert isinstance(order_book, list)
        assert len(order_book) > 0
        print(f"Order book entries: {len(order_book)}")

    @pytest.mark.slow
    @patch('requests.get')
    def test_get_real_time_price_real_data(self, mock_get):
        """تست دریافت قیمت لحظه‌ای با داده‌های واقعی (mocked)"""
        mock_response = MagicMock()
        mock_response.text = (
            '1010,1005,1015,1000,1012,1008'
        )
        mock_get.return_value = mock_response
        price_data = get_real_time_price_scraping(self.test_symbols['web_id'])
        assert isinstance(price_data, list)
        assert len(price_data) > 0
        print(f"Real-time price data: {len(price_data)} fields")

    @pytest.mark.slow
    @patch('requests.get')
    def test_get_trade_summary_real_data(self, mock_get):
        """تست دریافت خلاصه معاملات با داده‌های واقعی (mocked)"""
        mock_response = MagicMock()
        mock_response.text = (
            '08:30:00,1000,10,10000,123,456;08:31:00,1010,5,5050,124,457'
        )
        mock_get.return_value = mock_response
        summary = get_trade_summary_scraping(self.test_symbols['web_id'])
        assert isinstance(summary, dict)
        expected_keys = ['total_trades', 'total_volume', 'total_value',
                       'avg_price', 'max_price', 'min_price']
        for key in expected_keys:
            assert key in summary
            assert isinstance(summary[key], (int, float))
            assert summary[key] >= 0
        print(f"Trade summary: {summary}")

    def test_invalid_symbol_handling(self):
        """تست مدیریت نماد نامعتبر"""
        # نماد غیر عددی باید None برگرداند
        result = get_intraday_trades_scraping("invalid_symbol")
        assert result is None

        result = get_order_book_scraping("invalid_symbol")
        assert result is None

        result = get_real_time_price_scraping("invalid_symbol")
        assert result is None

        result = get_trade_summary_scraping("invalid_symbol")
        assert result is None

    @patch('requests.get')
    def test_trade_summary_calculation(self, mock_get):
        """تست محاسبات خلاصه معاملات (mocked)"""
        mock_response = MagicMock()
        mock_response.text = (
            '08:30:00,1000,10,10000,123,456;08:31:00,1010,5,5050,124,457'
        )
        mock_get.return_value = mock_response
        df = get_intraday_trades_scraping(self.test_symbols['web_id'])
        summary = get_trade_summary_scraping(self.test_symbols['web_id'])
        assert summary is not None
        expected_total_trades = len(df)
        expected_total_volume = df['volume'].astype(float).sum()
        expected_total_value = df['value'].astype(float).sum()
        expected_avg_price = df['price'].astype(float).mean()
        expected_max_price = df['price'].astype(float).max()
        expected_min_price = df['price'].astype(float).min()
        assert summary['total_trades'] == expected_total_trades
        assert abs(summary['total_volume'] - expected_total_volume) < 0.01
        assert abs(summary['total_value'] - expected_total_value) < 0.01
        assert abs(summary['avg_price'] - expected_avg_price) < 0.01
        assert abs(summary['max_price'] - expected_max_price) < 0.01
        assert abs(summary['min_price'] - expected_min_price) < 0.01

    @patch('requests.get')
    def test_data_consistency_across_functions(self, mock_get):
        """تست consistency داده‌ها بین توابع مختلف (mocked)"""
        mock_response = MagicMock()
        mock_response.text = (
            '08:30:00,1000,10,10000,123,456;08:31:00,1010,5,5050,124,457'
        )
        mock_get.return_value = mock_response
        trades_df = get_intraday_trades_scraping(self.test_symbols['web_id'])
        summary = get_trade_summary_scraping(self.test_symbols['web_id'])
        assert summary['total_trades'] == len(trades_df)
        total_volume = trades_df['volume'].astype(float).sum()
        assert abs(summary['total_volume'] - total_volume) < 0.01

    def test_error_handling_network_timeout(self):
        """تست مدیریت timeout شبکه"""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = TimeoutError("Connection timeout")

            result = get_intraday_trades_scraping(self.test_symbols['web_id'])
            assert result is None

            result = get_order_book_scraping(self.test_symbols['web_id'])
            assert result is None

            result = get_real_time_price_scraping(self.test_symbols['web_id'])
            assert result is None

    def test_error_handling_invalid_response(self):
        """تست مدیریت پاسخ نامعتبر (mocked)"""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = ""
            mock_get.return_value = mock_response
            result = get_intraday_trades_scraping(self.test_symbols['web_id'])
            assert result is None or (isinstance(result, pd.DataFrame) and result.empty)
            result = get_order_book_scraping(self.test_symbols['web_id'])
            assert result is None or result == []
            result = get_real_time_price_scraping(self.test_symbols['web_id'])
            assert result is None or result == []

    @patch('requests.get')
    def test_date_format_handling(self, mock_get):
        """تست مدیریت فرمت تاریخ (mocked)"""
        mock_response = MagicMock()
        mock_response.text = (
            '08:30:00,1000,10,10000,123,456'
        )
        mock_get.return_value = mock_response
        date_with_dash = "1402-01-01"
        df1 = get_intraday_trades_scraping(self.test_symbols['web_id'], date_with_dash)
        date_without_dash = "14020101"
        df2 = get_intraday_trades_scraping(self.test_symbols['web_id'], date_without_dash)
        assert isinstance(df1, pd.DataFrame)
        assert isinstance(df2, pd.DataFrame)
        assert df1.equals(df2)

    @patch('requests.get')
    def test_empty_data_handling(self, mock_get):
        """تست مدیریت داده‌های خالی (mocked)"""
        mock_response = MagicMock()
        mock_response.text = ''
        mock_get.return_value = mock_response
        summary = get_trade_summary_scraping("99999999999999999")
        assert isinstance(summary, dict)
        assert summary['total_trades'] == 0
        assert summary['total_volume'] == 0
        assert summary['total_value'] == 0

    @patch('requests.get')
    def test_data_types_and_ranges(self, mock_get):
        """تست نوع داده‌ها و محدوده مقادیر (mocked)"""
        mock_response = MagicMock()
        mock_response.text = (
            '08:30:00,1000,10,10000,123,456;08:31:00,1010,5,5050,124,457'
        )
        mock_get.return_value = mock_response
        df = get_intraday_trades_scraping(self.test_symbols['web_id'])
        assert pd.api.types.is_object_dtype(df['time'])
        assert pd.api.types.is_numeric_dtype(df['price'])
        assert pd.api.types.is_numeric_dtype(df['volume'])
        assert pd.api.types.is_numeric_dtype(df['value'])
        assert (df['price'] > 0).all()
        assert (df['volume'] > 0).all()
        assert (df['value'] > 0).all()
        time_pattern = r'^\d{2}:\d{2}:\d{2}$'
        assert df['time'].str.match(time_pattern).all()

    @patch('requests.get')
    def test_concurrent_requests_simulation(self, mock_get):
        """تست شبیه‌سازی درخواست‌های همزمان (mocked)"""
        import threading
        mock_response = MagicMock()
        mock_response.text = (
            '08:30:00,1000,10,10000,123,456;08:31:00,1010,5,5050,124,457'
        )
        mock_get.return_value = mock_response
        results = []
        def fetch_data():
            result = get_intraday_trades_scraping(self.test_symbols['web_id'])
            results.append(result)
        threads = []
        for i in range(3):
            t = threading.Thread(target=fetch_data)
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        assert len(results) == 3
        for result in results:
            assert result is not None or isinstance(result, pd.DataFrame)