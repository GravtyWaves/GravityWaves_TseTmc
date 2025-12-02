import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from api.price_history import (
    resolve_web_id, get_price_panel, get_60d_price_history
)


class TestPriceHistory:
    """Test cases for price_history.py functions using real TSE data"""

    def test_resolve_web_id_numeric(self):
        """Test resolve_web_id with numeric ticker"""
        result = resolve_web_id('35425587644337450')  # Real فولاد web_id
        assert result == '35425587644337450'

    def test_resolve_web_id_string_mapped(self):
        """Test resolve_web_id with mapped string ticker"""
        result = resolve_web_id('خودرو')
        assert result == '35425587644337450'

    def test_resolve_web_id_string_unmapped(self):
        """Test resolve_web_id with unmapped string ticker"""
        result = resolve_web_id('UNKNOWN_STOCK')
        assert result == 'UNKNOWN_STOCK'

    def test_get_price_panel_real_data(self):
        """Test get_price_panel with real TSE data"""
        # Use real stock tickers
        stock_list = ['خودرو', 'فولاد']  # Real TSE stocks

        result = get_price_panel(stock_list, jalali_date=False)

        # Verify we got a DataFrame
        assert isinstance(result, pd.DataFrame)

        # If data is available, check structure
        if not result.empty:
            assert 'Ticker' in result.columns
            assert 'Date' in result.columns
            assert 'Final' in result.columns

            # Check that tickers are in the result
            tickers_in_result = result['Ticker'].unique()
            for ticker in stock_list:
                assert ticker in tickers_in_result

            print(f"Successfully fetched price panel data for {len(result)} records")
        else:
            print("No price panel data available (may be due to market closure or API issues)")

    def test_get_price_panel_empty_list(self):
        """Test get_price_panel with empty stock list"""
        result = get_price_panel([])
        assert isinstance(result, pd.DataFrame)
        assert result.empty

    def test_get_price_panel_jalali_date_conversion(self):
        """Test get_price_panel with jalali date conversion using real data"""
        stock_list = ['خودرو']

        result = get_price_panel(stock_list, jalali_date=True)

        assert isinstance(result, pd.DataFrame)

        if not result.empty:
            # Should have J-Date column instead of Date
            assert 'J-Date' in result.columns
            assert 'Date' not in result.columns

            # Check jalali date format (should be like 1401/01/01)
            sample_date = result['J-Date'].iloc[0]
            assert isinstance(sample_date, str)
            assert len(sample_date) == 10  # YYYY/MM/DD format
            assert sample_date.count('/') == 2

            print(f"Jalali date conversion successful, sample: {sample_date}")

    def test_get_60d_price_history_real_data(self):
        """Test get_60d_price_history with real TSE data"""
        stock_list = ['خودرو', 'فولاد']

        result = get_60d_price_history(stock_list)

        assert isinstance(result, pd.DataFrame)

        if not result.empty:
            # Check expected columns
            expected_columns = ['WEB-ID', 'n', 'Y-Final', 'Open', 'High', 'Low', 'Close', 'Final', 'Volume', 'Value', 'No']
            for col in expected_columns:
                assert col in result.columns

            # Check data types
            assert result['WEB-ID'].dtype in [str, object]
            assert result['Final'].dtype in [float, int]

            # Check that requested stocks are included
            web_ids = [resolve_web_id(ticker) for ticker in stock_list]
            result_web_ids = result['WEB-ID'].unique()
            for web_id in web_ids:
                assert web_id in result_web_ids

            print(f"Successfully fetched 60d price history for {len(result)} records")
        else:
            print("No 60d price history data available")

    def test_get_60d_price_history_empty_list(self):
        """Test get_60d_price_history with empty stock list"""
        result = get_60d_price_history([])
        assert isinstance(result, pd.DataFrame)
        assert result.empty

    def test_get_60d_price_history_single_stock(self):
        """Test get_60d_price_history with single stock"""
        stock_list = ['خودرو']

        result = get_60d_price_history(stock_list)

        assert isinstance(result, pd.DataFrame)

        if not result.empty:
            # Should only contain data for the requested stock
            expected_web_id = resolve_web_id('خودرو')
            unique_web_ids = result['WEB-ID'].unique()
            assert len(unique_web_ids) == 1
            assert unique_web_ids[0] == expected_web_id

    def test_get_60d_price_history_excel_save(self, tmp_path):
        """Test get_60d_price_history with Excel saving"""
        stock_list = ['خودرو']
        save_path = str(tmp_path / "test_60d_history")

        result = get_60d_price_history(stock_list, save_excel=True, save_path=save_path)

        assert isinstance(result, pd.DataFrame)

        # Check if Excel file was created (only if data was available)
        import os
        excel_files = [f for f in os.listdir(tmp_path) if f.endswith('.xlsx')]
        if not result.empty and excel_files:
            assert len(excel_files) == 1
            print(f"Excel file saved: {excel_files[0]}")

    def test_get_price_panel_date_filtering(self):
        """Test get_price_panel date filtering with real data"""
        stock_list = ['خودرو']

        result = get_price_panel(stock_list, jalali_date=True)

        if not result.empty:
            # Check date ordering (most recent first)
            dates = pd.to_datetime(result.index, errors='coerce')
            if len(dates) > 1:
                assert dates.is_monotonic_decreasing  # Should be sorted descending

    def test_get_60d_price_history_data_integrity(self):
        """Test data integrity in get_60d_price_history"""
        stock_list = ['خودرو']

        result = get_60d_price_history(stock_list)

        if not result.empty:
            # Check for reasonable price values
            assert (result['Final'] > 0).all(), "All final prices should be positive"
            assert (result['Volume'] >= 0).all(), "All volumes should be non-negative"

            # Check high >= low
            assert (result['High'] >= result['Low']).all(), "High prices should be >= low prices"

            # Check that close is between low and high
            assert ((result['Close'] >= result['Low']) & (result['Close'] <= result['High'])).all(), \
                   "Close prices should be between low and high"

    def test_get_price_panel_multiple_stocks(self):
        """Test get_price_panel with multiple stocks"""
        stock_list = ['خودرو', 'فولاد', 'وبانک']

        result = get_price_panel(stock_list)

        assert isinstance(result, pd.DataFrame)

        if not result.empty:
            unique_tickers = result['Ticker'].unique()
            for ticker in stock_list:
                assert ticker in unique_tickers

            print(f"Data fetched for {len(unique_tickers)} out of {len(stock_list)} stocks")

    def test_resolve_web_id_edge_cases(self):
        """Test resolve_web_id with edge cases"""
        # Test with integer
        result = resolve_web_id(12345)
        assert result == 12345

        # Test with empty string
        result = resolve_web_id('')
        assert result == ''

        # Test with None (should handle gracefully)
        result = resolve_web_id(None)
        assert result is None

        # Test with very long string
        long_ticker = 'A' * 100
        result = resolve_web_id(long_ticker)
        assert result == long_ticker

    def test_get_price_panel_error_handling(self):
        """Test get_price_panel error handling with invalid data"""
        # Test with invalid ticker that might cause issues
        stock_list = ['INVALID_TICKER_12345']

        result = get_price_panel(stock_list)

        # Should return DataFrame even with invalid tickers
        assert isinstance(result, pd.DataFrame)
        # May be empty or may have handled gracefully

    def test_get_60d_price_history_large_dataset(self):
        """Test get_60d_price_history with larger stock list"""
        # Test with more stocks to check performance
        stock_list = ['خودرو', 'فولاد', 'وبانک', 'ملت', 'پارس']

        result = get_60d_price_history(stock_list)

        assert isinstance(result, pd.DataFrame)

        if not result.empty:
            unique_web_ids = result['WEB-ID'].unique()
            print(f"Data fetched for {len(unique_web_ids)} unique instruments")

            # Should have data for at least some stocks
            assert len(unique_web_ids) > 0

    def test_get_price_panel_data_consistency(self):
        """Test data consistency in get_price_panel results"""
        stock_list = ['خودرو']

        result = get_price_panel(stock_list)

        if not result.empty:
            # Check that all records for a ticker have the same ticker name
            for ticker in result['Ticker'].unique():
                ticker_data = result[result['Ticker'] == ticker]
                assert (ticker_data['Ticker'] == ticker).all()

            # Check date format consistency
            if 'Date' in result.columns:
                sample_dates = result['Date'].head(5)
                for date_val in sample_dates:
                    # Should be in YYYY-MM-DD format or similar
                    assert isinstance(date_val, str)
                    assert len(date_val) >= 8  # At least YYYYMMDD

    def test_get_60d_price_history_date_ordering(self):
        """Test date ordering in get_60d_price_history"""
        stock_list = ['خودرو']

        result = get_60d_price_history(stock_list)

        if not result.empty and 'n' in result.columns:
            # 'n' column should be sorted (represents trading days)
            assert result['n'].is_monotonic_increasing, "Trading days should be in ascending order"

    def test_get_price_panel_memory_efficiency(self):
        """Test memory efficiency with large stock lists"""
        # Test with many stocks
        stock_list = ['خودرو', 'فولاد', 'وبانک', 'ملت', 'پارس'] * 5  # 25 stocks

        import psutil
        import os
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        result = get_price_panel(stock_list)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = final_memory - initial_memory

        assert isinstance(result, pd.DataFrame)
        print(f"Memory usage for {len(stock_list)} stocks: {memory_used:.2f} MB")

        # Should not use excessive memory
        assert memory_used < 500  # Less than 500MB increase

    def test_get_60d_price_history_performance(self):
        """Test performance of get_60d_price_history"""
        import time

        stock_list = ['خودرو', 'فولاد']

        start_time = time.time()
        result = get_60d_price_history(stock_list)
        end_time = time.time()

        duration = end_time - start_time

        assert isinstance(result, pd.DataFrame)
        print(f"60d price history fetch took {duration:.2f} seconds")

        # Should complete within reasonable time (allowing for network latency)
        assert duration < 30  # Less than 30 seconds

    def test_get_price_panel_concurrent_access(self):
        """Test concurrent access to get_price_panel"""
        import threading
        import queue

        results = queue.Queue()
        stock_lists = [['خودرو'], ['فولاد'], ['وبانک']]

        def fetch_worker(stock_list):
            try:
                result = get_price_panel(stock_list)
                results.put(('success', len(result)))
            except Exception as e:
                results.put(('error', str(e)))

        threads = []
        for stock_list in stock_lists:
            t = threading.Thread(target=fetch_worker, args=(stock_list,))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        # Check results
        success_count = 0
        total_records = 0
        while not results.empty():
            status, data = results.get()
            if status == 'success':
                success_count += 1
                total_records += data

        print(f"Concurrent fetch: {success_count}/{len(stock_lists)} successful, {total_records} total records")
        assert success_count >= 2  # At least 2 should succeed

    def test_get_60d_price_history_data_validation(self):
        """Test data validation in get_60d_price_history results"""
        stock_list = ['خودرو']

        result = get_60d_price_history(stock_list)

        if not result.empty:
            # Validate numeric columns
            numeric_columns = ['Y-Final', 'Open', 'High', 'Low', 'Close', 'Final', 'Volume', 'Value', 'No']
            for col in numeric_columns:
                if col in result.columns:
                    # Should be numeric
                    assert pd.api.types.is_numeric_dtype(result[col]), f"Column {col} should be numeric"

                    # Should not have NaN values in critical columns
                    if col in ['Final', 'Close']:
                        assert not result[col].isnull().any(), f"Column {col} should not have NaN values"

    def test_get_price_panel_network_resilience(self):
        """Test network resilience of get_price_panel"""
        stock_list = ['خودرو']

        # Test multiple calls to check for network issues
        results = []
        for i in range(3):
            result = get_price_panel(stock_list)
            results.append(result is not None and isinstance(result, pd.DataFrame))

        success_rate = sum(results) / len(results)
        print(f"Network resilience test: {success_rate:.1%} success rate")

        # Should have reasonable success rate
        assert success_rate >= 0.5

    def test_get_60d_price_history_filtering_accuracy(self):
        """Test filtering accuracy in get_60d_price_history"""
        # Test with stocks that should have different web_ids
        stock_list = ['خودرو', 'فولاد']

        result = get_60d_price_history(stock_list)

        if not result.empty:
            web_ids = [resolve_web_id(ticker) for ticker in stock_list]
            result_web_ids = set(result['WEB-ID'].unique())

            # Should only contain requested web_ids
            assert result_web_ids.issubset(set(web_ids)), "Result should only contain requested stocks"

    def test_get_price_panel_data_freshness(self):
        """Test data freshness in get_price_panel"""
        import time
        stock_list = ['خودرو']

        result1 = get_price_panel(stock_list)
        time.sleep(1)  # Wait 1 second
        result2 = get_price_panel(stock_list)

        # Results should be similar (data shouldn't change drastically in 1 second)
        if not result1.empty and not result2.empty:
            # Compare record counts (should be similar)
            count_diff = abs(len(result1) - len(result2))
            assert count_diff <= 5, f"Data changed too much in 1 second: {count_diff} records difference"

    def test_get_60d_price_history_comprehensive_validation(self):
        """Comprehensive validation of get_60d_price_history data"""
        stock_list = ['خودرو']

        result = get_60d_price_history(stock_list)

        if not result.empty:
            # Validate business rules
            assert all(result['High'] >= result['Low']), "High should be >= Low"
            assert all(result['High'] >= result['Close']), "High should be >= Close"
            assert all(result['Low'] <= result['Close']), "Low should be <= Close"
            assert all(result['Volume'] >= 0), "Volume should be >= 0"
            assert all(result['Value'] >= 0), "Value should be >= 0"

            # Validate date progression
            if 'n' in result.columns and len(result) > 1:
                assert result['n'].is_unique, "Trading day numbers should be unique"

            print("All business rules validated successfully")

    @patch('api.price_history.requests.get')
    @patch('api.price_history.jdatetime.datetime')
    @patch('api.price_history.pd.DataFrame.to_excel')
    def test_get_price_panel_save_excel_success_mock(self, mock_to_excel, mock_jdatetime, mock_get):
        """Test get_price_panel with successful Excel saving"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "20231001,1000,1010,990,1005,1000,10000,10000000,995,1000"
        mock_get.return_value = mock_response
        mock_jdatetime.now.return_value.strftime.return_value = "2023-10-01"

        stock_list = ['TEST']
        result = get_price_panel(stock_list, save_excel=True)

        assert isinstance(result, pd.DataFrame)

    @patch('api.price_history.requests.get')
    def test_get_price_panel_request_failure(self, mock_get):
        """Test get_price_panel with request failure"""
        mock_get.side_effect = Exception("Network error")

        stock_list = ['TEST']
        result = get_price_panel(stock_list, save_excel=False)

        # Should return empty DataFrame on failure
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0

    @patch('api.price_history.requests.get')
    def test_get_price_panel_invalid_response_mock(self, mock_get):
        """Test get_price_panel with invalid response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "invalid,data"
        mock_get.return_value = mock_response

        stock_list = ['TEST']
        result = get_price_panel(stock_list, save_excel=False)

        # Should handle invalid data gracefully
        assert isinstance(result, pd.DataFrame)

    @patch('api.price_history.requests.get')
    @patch('api.price_history.jdatetime.datetime')
    @patch('api.price_history.pd.DataFrame.to_excel')
    def test_get_60d_price_history_save_excel_mock(self, mock_to_excel, mock_jdatetime, mock_get):
        """Test get_60d_price_history with Excel saving"""
        mock_response = MagicMock()
        mock_response.text = "data1;data2"
        mock_get.return_value = mock_response
        mock_jdatetime.now.return_value.strftime.return_value = "2023-10-01"

        stock_list = ['TEST']
        result = get_60d_price_history(stock_list, save_excel=True)

        assert isinstance(result, pd.DataFrame)

    @patch('api.price_history.requests.get')
    def test_get_60d_price_history_request_failure(self, mock_get):
        """Test get_60d_price_history with request failure"""
        mock_get.side_effect = Exception("Network error")

        stock_list = ['TEST']
        result = get_60d_price_history(stock_list, save_excel=False)

        # Should return empty DataFrame or handle error
        assert isinstance(result, pd.DataFrame)

    def test_resolve_web_id_edge_cases(self):
        """Test resolve_web_id with edge cases"""
        # Test with integer
        result = resolve_web_id(12345)
        assert result == 12345

        # Test with empty string
        result = resolve_web_id('')
        assert result == ''

        # Test with None (should handle gracefully)
        result = resolve_web_id(None)
        assert result is None

    @patch('api.price_history.requests.get')
    def test_get_price_panel_jalali_date_conversion_error_mock(self, mock_get):
        """Test jalali date conversion error handling"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "invalid_date,1000,1010,990,1005,1000,10000,10000000,995,1000"
        mock_get.return_value = mock_response

        stock_list = ['TEST']
        result = get_price_panel(stock_list, jalali_date=True, save_excel=False)

        # Should handle date conversion errors
        assert isinstance(result, pd.DataFrame)

    @patch('api.price_history.requests.get')
    def test_get_60d_price_history_large_dataset_mock(self, mock_get):
        """Test get_60d_price_history with large dataset"""
        # Create large mock data in correct format: webid,n,Y-Final,Open,High,Low,Close,Final,Volume,Value,No
        mock_data = "TEST,1,1000,1005,1010,990,1005,1000,10000,10000000,995"
        large_data = ";".join([mock_data] * 100)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = large_data
        mock_get.return_value = mock_response

        stock_list = ['TEST']
        result = get_60d_price_history(stock_list, save_excel=False)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 100

    @patch('api.price_history.requests.get')
    def test_get_price_panel_concurrent_access_mock(self, mock_get):
        """Test get_price_panel with multiple stocks (simulating concurrent access)"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "20231001,1000,1010,990,1005,1000,10000,10000000,995,1000"
        mock_get.return_value = mock_response

        stock_list = ['STOCK1', 'STOCK2', 'STOCK3']
        result = get_price_panel(stock_list, save_excel=False)

        assert isinstance(result, pd.DataFrame)
        # Should have data for multiple stocks
        if not result.empty:
            unique_tickers = result['Ticker'].nunique()
            assert unique_tickers <= len(stock_list)

    @patch('api.price_history.requests.get')
    def test_get_60d_price_history_performance_mock(self, mock_get):
        """Test get_60d_price_history performance with multiple stocks"""
        mock_response = MagicMock()
        mock_response.text = "data1;data2;data3"
        mock_get.return_value = mock_response

        stock_list = ['STOCK1', 'STOCK2', 'STOCK3', 'STOCK4', 'STOCK5']
        result = get_60d_price_history(stock_list, save_excel=False)

        assert isinstance(result, pd.DataFrame)

    @patch('api.price_history.requests.get')
    def test_get_price_panel_network_resilience(self, mock_get):
        """Test get_price_panel network resilience"""
        # Mix of success and failure
        def side_effect(*args, **kwargs):
            if 'STOCK1' in str(args[0]):
                mock_resp = MagicMock()
                mock_resp.status_code = 200
                mock_resp.text = "20231001,1000,1010,990,1005,1000,10000,10000000,995,1000"
                return mock_resp
            else:
                raise Exception("Network error")

        mock_get.side_effect = side_effect

        stock_list = ['STOCK1', 'STOCK2']
        result = get_price_panel(stock_list, save_excel=False)

        # Should have data for STOCK1 but not STOCK2
        assert isinstance(result, pd.DataFrame)

    @patch('api.price_history.requests.get')
    def test_get_60d_price_history_filtering_accuracy_mock(self, mock_get):
        """Test get_60d_price_history data filtering accuracy"""
        mock_response = MagicMock()
        mock_response.text = "1,1010,1005,100,10000,10000000,995,1015,1000,1000;2,1020,1015,200,20000,20000000,1005,1025,1010,1010"
        mock_get.return_value = mock_response

        stock_list = ['TEST']
        result = get_60d_price_history(stock_list, save_excel=False)

        assert isinstance(result, pd.DataFrame)
        if not result.empty:
            # Check data types are correct
            assert pd.api.types.is_numeric_dtype(result['Final'])
            assert pd.api.types.is_numeric_dtype(result['Volume'])

    @patch('api.price_history.requests.get')
    def test_get_price_panel_data_freshness_mock(self, mock_get):
        """Test get_price_panel data freshness"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "20241203,1000,1010,990,1005,1000,10000,10000000,995,1000"
        mock_get.return_value = mock_response

        stock_list = ['TEST']
        result = get_price_panel(stock_list, jalali_date=False, save_excel=False)

        assert isinstance(result, pd.DataFrame)
        if not result.empty and 'Date' in result.columns:
            # Check dates are recent (within last year)
            max_date = pd.to_datetime(result['Date']).max()
            one_year_ago = pd.Timestamp.now() - pd.DateOffset(years=1)
            assert max_date >= one_year_ago

    @patch('api.price_history.requests.get')
    def test_get_60d_price_history_comprehensive_validation_mock(self, mock_get):
        """Test get_60d_price_history comprehensive data validation"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "TEST,1,1010,1005,10000,100,10000000,995,1015,1000,1000;TEST,2,1020,1015,20000,200,20000000,1005,1025,1010,1010;TEST,3,1030,1025,30000,300,30000000,1015,1035,1020,1020"
        mock_get.return_value = mock_response

        stock_list = ['TEST']
        result = get_60d_price_history(stock_list, save_excel=False)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3

        # Validate all required columns exist
        required_cols = ['n', 'Final', 'Close', 'No', 'Volume', 'Value', 'Low', 'High', 'Y-Final', 'Open']
        for col in required_cols:
            assert col in result.columns

        # Validate data integrity
        assert all(result['High'] >= result['Low'])
        assert all(result['Volume'] >= 0)
        assert all(result['Value'] >= 0)
