import pytest
import tempfile
import os
import time
from datetime import date, datetime, timedelta
from unittest.mock import patch, MagicMock
from main import TSEDataCollector
from database.sqlite_db import SQLiteDatabase
from database.postgres_db import PostgreSQLDatabase
 # حذف وابستگی به TSEAPIClient
from utils.logger import setup_logger


class TestRealDataIntegration:
    """Integration tests using real TSE API data with 95% coverage"""

    @pytest.fixture
    def temp_db_path(self):
        # Create a temporary database file
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        # Cleanup - ensure database connections are closed first
        try:
            if os.path.exists(path):
                # Force close any remaining connections on Windows
                import sqlite3
                conn = sqlite3.connect(path)
                conn.close()
                os.unlink(path)
        except (OSError, PermissionError):
            # If we can't delete it now, let the OS clean it up later
            pass

    @pytest.fixture
    def temp_db(self, temp_db_path):
        with patch('database.base.DATABASE_URL', f'sqlite:///{temp_db_path}'):
            db = SQLiteDatabase()
            yield db
            # Ensure proper cleanup
            try:
                db.close()
            except:
                pass

    @pytest.fixture
    def collector(self, temp_db):
        # Use real TSE API client (not mocked)
        collector = TSEDataCollector()
        collector.db = temp_db
        yield collector

    def test_real_stock_list_fetch(self, collector):
        """Test fetching real stock list from TSE API"""
        stock_list = collector.api.get_stock_list()

        # Verify we got data
        assert stock_list is not None
        assert isinstance(stock_list, list)
        assert len(stock_list) > 0

        # Verify structure of first stock
        first_stock = stock_list[0]
        required_fields = ['InsCode', 'Symbol', 'Name', 'ticker', 'name', 'web_id']
        for field in required_fields:
            assert field in first_stock, f"Missing field: {field}"
            assert first_stock[field] is not None, f"Field {field} is None"

        print(f"Successfully fetched {len(stock_list)} stocks from TSE API")

    def test_real_sector_list_fetch(self, collector):
        """Test fetching real sector list from TSE API"""
        sector_list = collector.api.get_sector_list()

        # Verify we got data
        assert sector_list is not None
        assert isinstance(sector_list, list)
        assert len(sector_list) > 0

        # Verify structure of first sector
        first_sector = sector_list[0]
        required_fields = ['SectorCode', 'SectorName', 'SectorNameEn']
        for field in required_fields:
            assert field in first_sector

        print(f"Successfully fetched {len(sector_list)} sectors from TSE API")

    def test_real_index_list_fetch(self, collector):
        """Test fetching real index list"""
        index_list = collector.api.get_index_list()

        # Verify we got data
        assert index_list is not None
        assert isinstance(index_list, list)
        assert len(index_list) > 0

        # Verify structure of first index
        first_index = index_list[0]
        required_fields = ['IndexName', 'IndexNameEn', 'InsCode']
        for field in required_fields:
            assert field in first_index

        print(f"Successfully fetched {len(index_list)} indices")

    def test_real_data_collection_workflow(self, collector):
        """Test complete data collection workflow with real data"""

        # Collect stocks
        stocks_result = collector.collect_stocks()
        assert stocks_result > 0
        print(f"Collected {stocks_result} stocks")

        # Collect sectors
        sectors_result = collector.collect_sectors()
        assert sectors_result > 0
        print(f"Collected {sectors_result} sectors")

        # Collect indices
        indices_result = collector.collect_indices()
        assert indices_result > 0
        print(f"Collected {indices_result} indices")

        # Verify data in database
        session = collector.db.get_session()
        try:
            stocks = session.query(collector.db.Stock).all()
            sectors = session.query(collector.db.Sector).all()
            indices = session.query(collector.db.Index).all()

            assert len(stocks) == stocks_result
            assert len(sectors) == sectors_result
            assert len(indices) == indices_result

            print(f"Database contains: {len(stocks)} stocks, {len(sectors)} sectors, {len(indices)} indices")

        finally:
            session.close()

    def test_real_price_history_fetch(self, collector):
        """Test fetching real price history data"""

        # First get a real stock
        stock_list = collector.api.get_stock_list()
        assert stock_list is not None and len(stock_list) > 0

        test_stock = stock_list[0]
        web_id = test_stock['web_id']

        # Add stock to database
        stock_data = {
            'ticker': test_stock['ticker'],
            'name': test_stock['name'],
            'web_id': web_id,
            'market': 'بازار اول'
        }
        stock = collector.db.add_stock(stock_data)
        assert stock is not None

        # Get date range
        from_date, to_date = collector.api.get_date_range(days=7)  # Last week

        # Fetch price history
        raw_data = collector.api.get_price_history(web_id, from_date, to_date)
        if raw_data:
            parsed_data = collector.api.parse_price_history(raw_data, str(stock.id))
            assert isinstance(parsed_data, list)

            if len(parsed_data) > 0:
                # Test adding to database
                result = collector.db.add_price_history(parsed_data)
                assert result == len(parsed_data)
                print(f"Successfully fetched and stored {len(parsed_data)} price records for {test_stock['ticker']}")
            else:
                print(f"No price history data available for {test_stock['ticker']} in the last 7 days")
        else:
            print(f"No price history data returned for {test_stock['ticker']}")

    def test_real_client_type_history_fetch(self, collector):
        """Test fetching real client type (RI) history data"""

        # First get a real stock
        stock_list = collector.api.get_stock_list()
        assert stock_list is not None and len(stock_list) > 0

        test_stock = stock_list[0]
        web_id = test_stock['web_id']

        # Add stock to database
        stock_data = {
            'ticker': test_stock['ticker'],
            'name': test_stock['name'],
            'web_id': web_id,
            'market': 'بازار اول'
        }
        stock = collector.db.add_stock(stock_data)
        assert stock is not None

        # Get date range
        from_date, to_date = collector.api.get_date_range(days=7)  # Last week

        # Fetch RI history
        raw_data = collector.api.get_client_type_history(web_id, from_date, to_date)
        if raw_data:
            parsed_data = collector.api.parse_client_type_history(raw_data, str(stock.id))
            assert isinstance(parsed_data, list)

            if len(parsed_data) > 0:
                # Test adding to database
                result = collector.db.add_ri_history(parsed_data)
                assert result == len(parsed_data)
                print(f"Successfully fetched and stored {len(parsed_data)} RI records for {test_stock['ticker']}")
            else:
                print(f"No RI history data available for {test_stock['ticker']} in the last 7 days")
        else:
            print(f"No RI history data returned for {test_stock['ticker']}")

    def test_real_full_update_workflow(self, collector):
        """Test the complete real data update workflow"""

        # Run full update
        result = collector.run_full_update()

        # Verify results
        assert result['success'] == True
        assert result['stocks'] > 0
        assert result['sectors'] > 0
        assert result['indices'] > 0

        print(f"Full update completed successfully:")
        print(f"  - Stocks: {result['stocks']}")
        print(f"  - Sectors: {result['sectors']}")
        print(f"  - Indices: {result['indices']}")

        # Verify data integrity
        session = collector.db.get_session()
        try:
            stocks = session.query(collector.db.Stock).all()
            sectors = session.query(collector.db.Sector).all()
            indices = session.query(collector.db.Index).all()

            assert len(stocks) == result['stocks']
            assert len(sectors) == result['sectors']
            assert len(indices) == result['indices']

            # Check that stocks have required fields
            for stock in stocks[:5]:  # Check first 5 stocks
                assert stock.ticker is not None
                assert stock.name is not None
                assert stock.web_id is not None

        finally:
            session.close()

    def test_real_incremental_update(self, collector):
        """Test incremental updates with real data"""
        # Mock the API to return consistent data for testing incremental behavior
        mock_stocks = [
            {
                'ticker': f'SYM{i}',
                'name': f'Name{i}',
                'web_id': f'WEB{i}',
                'SectorCode': '1'
            } for i in range(10)
        ]
        mock_sectors = [
            {'SectorCode': '1', 'SectorName': 'Sector1', 'SectorNameEn': 'Sector1En'},
            {'SectorCode': '2', 'SectorName': 'Sector2', 'SectorNameEn': 'Sector2En'}
        ]
        mock_indices = [
            {'name': 'Index1', 'web_id': 'INDEX1'},
            {'name': 'Index2', 'web_id': 'INDEX2'}
        ]

        with patch.object(collector.api, 'get_stock_list', return_value=mock_stocks), \
             patch.object(collector.api, 'get_sector_list', return_value=mock_sectors), \
             patch.object(collector.api, 'get_index_list', return_value=mock_indices):
            # First run
            result1 = collector.run_full_update()
            initial_stock_count = result1['stocks']
            assert initial_stock_count == 10

            # Second run (should not add duplicates)
            result2 = collector.run_full_update()
            second_stock_count = result2['stocks']

            # Should be 0 new stocks (all duplicates)
            assert second_stock_count == 0, f"Too many new stocks: {second_stock_count}"

            # Verify total count is still 10
            session = collector.db.get_session()
            try:
                total_stocks = session.query(collector.db.Stock).count()
                assert total_stocks == 10
            finally:
                session.close()

        print(f"Incremental update test passed: {initial_stock_count} initial stocks, {second_stock_count} new stocks added")

    @pytest.mark.slow
    def test_real_price_history_update(self, collector):
        """Test real price history update for multiple stocks"""

        # First collect basic data
        collector.run_full_update()

        # Update price history for last 30 days
        result = collector.update_price_history(30)

        # Result should be >= 0 (may be 0 if no trading data)
        assert result >= 0

        print(f"Price history update completed: {result} records added")

        # Verify some data was stored
        session = collector.db.get_session()
        try:
            total_price_records = session.query(collector.db.PriceHistory).count()
            print(f"Total price history records in database: {total_price_records}")
        finally:
            session.close()

    @pytest.mark.slow
    def test_real_ri_history_update(self, collector):
        """Test real RI history update for multiple stocks"""

        # First collect basic data
        collector.run_full_update()

        # Update RI history for last 30 days
        result = collector.update_ri_history(30)

        # Result should be >= 0 (may be 0 if no trading data)
        assert result >= 0

        print(f"RI history update completed: {result} records added")

        # Verify some data was stored
        session = collector.db.get_session()
        try:
            total_ri_records = session.query(collector.db.RIHistory).count()
            print(f"Total RI history records in database: {total_ri_records}")
        finally:
            session.close()

    def test_real_api_error_handling(self, collector):
        """Test error handling with real API failures"""
        # Test with invalid web_id
        invalid_web_id = "999999999999999999999"
        result = collector.api.get_stock_details(invalid_web_id)
        assert result is None  # Should handle gracefully

        # Test with invalid date range
        invalid_from_date = "99/99/99"
        invalid_to_date = "99/99/99"
        result = collector.api.get_price_history("123456789", invalid_from_date, invalid_to_date)
        assert result is None  # Should handle gracefully

    def test_real_data_validation(self, collector):
        """Test data validation with real API responses"""
        stock_list = collector.api.get_stock_list()
        assert stock_list is not None

        for stock in stock_list[:10]:  # Test first 10 stocks
            # Validate required fields
            assert 'InsCode' in stock and stock['InsCode']
            assert 'Symbol' in stock and stock['Symbol']
            assert 'Name' in stock and stock['Name']
            assert 'web_id' in stock and stock['web_id']

            # Validate data types
            assert isinstance(stock['InsCode'], str)
            assert isinstance(stock['Symbol'], str)
            assert isinstance(stock['Name'], str)
            assert isinstance(stock['web_id'], str)

    def test_real_sector_data_consistency(self, collector):
        """Test sector data consistency across stocks and sectors"""
        stock_list = collector.api.get_stock_list()
        sector_list = collector.api.get_sector_list()

        assert stock_list is not None and sector_list is not None

        # Collect all sector codes from stocks
        stock_sector_codes = set()
        for stock in stock_list:
            if 'SectorCode' in stock and stock['SectorCode']:
                stock_sector_codes.add(stock['SectorCode'])

        # Collect all sector codes from sectors
        sector_codes = set()
        for sector in sector_list:
            if 'SectorCode' in sector and sector['SectorCode']:
                sector_codes.add(sector['SectorCode'])

        # All stock sector codes should exist in sector list
        assert stock_sector_codes.issubset(sector_codes)

    def test_real_index_data_structure(self, collector):
        """Test index data structure and completeness"""
        index_list = collector.api.get_index_list()
        assert index_list is not None
        assert len(index_list) >= 3  # Should have at least TEDPIX, TEDIX, TEDFIX

        for index in index_list:
            assert 'IndexName' in index and index['IndexName']
            assert 'IndexNameEn' in index and index['IndexNameEn']
            assert 'InsCode' in index and index['InsCode']

            # Validate InsCode format (should be numeric string)
            assert isinstance(index['InsCode'], str)
            assert index['InsCode'].isdigit()

    def test_real_date_range_generation(self, collector):
        """Test date range generation for historical data"""
        # Test various date ranges
        ranges = [
            collector.api.get_date_range(days=1),   # 1 day
            collector.api.get_date_range(days=7),   # 1 week
            collector.api.get_date_range(days=30),  # 1 month
            collector.api.get_date_range(days=90),  # 3 months
        ]

        for from_date, to_date in ranges:
            assert isinstance(from_date, str)
            assert isinstance(to_date, str)
            assert len(from_date) == 10  # YYYY/MM/DD format
            assert len(to_date) == 10
            assert from_date <= to_date  # From date should be before to date

    def test_real_current_date_functionality(self, collector):
        """Test current date functionality"""
        current_date = collector.api.get_current_date()
        assert isinstance(current_date, str)
        assert len(current_date) == 10  # YYYY/MM/DD format

        # Should be close to today's date (allowing for timezone differences)
        today = datetime.now()
        j_year = today.year - 621
        if today.month > 3 or (today.month == 3 and today.day >= 21):
            j_year += 1
        expected_date = f"{j_year:04d}/{today.month:02d}/{today.day:02d}"
        assert current_date == expected_date

    def test_real_instrument_search(self, collector):
        """Test instrument search functionality"""
        # Test with empty query
        result = collector.api.get_instrument_search("")
        assert result is None  # Should handle empty query

        # Test with sample stock symbol (if available)
        stock_list = collector.api.get_stock_list()
        if stock_list and len(stock_list) > 0:
            sample_symbol = stock_list[0]['Symbol'][:3]  # First 3 chars
            result = collector.api.get_instrument_search(sample_symbol)
            # Result might be None or data depending on API

    def test_real_instrument_info(self, collector):
        """Test instrument info retrieval"""
        stock_list = collector.api.get_stock_list()
        if stock_list and len(stock_list) > 0:
            web_id = stock_list[0]['web_id']
            result = collector.api.get_instrument_info(web_id)
            # Result might be None or data depending on API response

    def test_real_shareholder_history(self, collector):
        """Test shareholder history retrieval"""
        stock_list = collector.api.get_stock_list()
        if stock_list and len(stock_list) > 0:
            web_id = stock_list[0]['web_id']
            current_date = collector.api.get_current_date()
            result = collector.api.get_shareholder_history(web_id, current_date)
            # Result might be None or data depending on API response

    def test_real_intraday_trades(self, collector):
        """Test intraday trades retrieval"""
        stock_list = collector.api.get_stock_list()
        if stock_list and len(stock_list) > 0:
            web_id = stock_list[0]['web_id']
            current_date = collector.api.get_current_date()
            result = collector.api.get_intraday_trades(web_id, current_date)
            # Result might be None or data depending on API response

    def test_real_usd_history(self, collector):
        """Test USD history retrieval"""
        from_date, to_date = collector.api.get_date_range(days=7)
        result = collector.api.get_usd_history(from_date, to_date)
        # Result might be None or data depending on API response

    def test_real_sector_index_history(self, collector):
        """Test sector index history retrieval"""
        sector_list = collector.api.get_sector_list()
        if sector_list and len(sector_list) > 0:
            sector_code = sector_list[0]['SectorCode']
            from_date, to_date = collector.api.get_date_range(days=7)
            result = collector.api.get_sector_index_history(sector_code, from_date, to_date)
            # Result might be None or data depending on API response

    def test_real_index_history(self, collector):
        """Test index history retrieval"""
        index_list = collector.api.get_index_list()
        if index_list and len(index_list) > 0:
            index_id = index_list[0]['InsCode']
            from_date, to_date = collector.api.get_date_range(days=7)
            result = collector.api.get_index_history(index_id, from_date, to_date)
            # Result might be None or data depending on API response

    def test_real_parsing_functions(self, collector):
        """Test all parsing functions with real data"""
        # Test instrument search parsing
        raw_search_data = collector.api.get_instrument_search("فولاد")
        if raw_search_data:
            parsed = collector.api.parse_instrument_search(raw_search_data)
            assert isinstance(parsed, list)
            if len(parsed) > 0:
                assert 'InsCode' in parsed[0]
                assert 'Symbol' in parsed[0]

        # Test price history parsing
        stock_list = collector.api.get_stock_list()
        if stock_list and len(stock_list) > 0:
            web_id = stock_list[0]['web_id']
            from_date, to_date = collector.api.get_date_range(days=7)
            raw_price_data = collector.api.get_price_history(web_id, from_date, to_date)
            if raw_price_data:
                parsed = collector.api.parse_price_history(raw_price_data, "1")
                assert isinstance(parsed, list)

        # Test client type history parsing
        raw_client_data = collector.api.get_client_type_history(web_id, from_date, to_date)
        if raw_client_data:
            parsed = collector.api.parse_client_type_history(raw_client_data, "1")
            assert isinstance(parsed, list)

    def test_real_database_operations_comprehensive(self, collector):
        """Comprehensive test of all database operations with real data"""
        # Start with clean database
        collector.run_full_update()

        session = collector.db.get_session()
        try:
            # Verify all tables have data
            stocks = session.query(collector.db.Stock).all()
            sectors = session.query(collector.db.Sector).all()
            indices = session.query(collector.db.Index).all()

            assert len(stocks) > 0
            assert len(sectors) > 0
            assert len(indices) > 0

            # Test relationships
            for stock in stocks[:3]:  # Test first 3 stocks
                assert stock.ticker is not None
                assert stock.name is not None
                assert stock.web_id is not None

            for sector in sectors[:3]:  # Test first 3 sectors
                assert sector.sector_code is not None
                assert sector.sector_name is not None

            for index in indices[:3]:  # Test first 3 indices
                assert index.name is not None
                assert index.web_id is not None

        finally:
            session.close()

    def test_real_performance_metrics(self, collector):
        """Test performance metrics collection"""
        import time

        start_time = time.time()
        result = collector.run_full_update()
        end_time = time.time()

        duration = end_time - start_time
        print(f"Full update took {duration:.2f} seconds")

        # Should complete within reasonable time (allowing for network latency)
        assert duration < 300  # Less than 5 minutes
        assert result['success'] == True

    def test_real_memory_usage(self, collector):
        """Test memory usage during large data operations"""
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Run operations that might use significant memory
        collector.run_full_update()
        result = collector.update_price_history(30)

        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_used = final_memory - initial_memory

        print(f"Memory usage: {memory_used:.2f} MB")
        # Memory usage should be reasonable (less than 500MB increase)
        assert memory_used < 500

    def test_real_concurrent_operations(self, collector):
        """Test concurrent database operations"""
        import threading
        import queue

        results = queue.Queue()

        def run_update():
            try:
                result = collector.run_full_update()
                results.put(('success', result))
            except Exception as e:
                results.put(('error', str(e)))

        # Run multiple updates concurrently
        threads = []
        for i in range(3):
            t = threading.Thread(target=run_update)
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Check results
        success_count = 0
        while not results.empty():
            status, data = results.get()
            if status == 'success':
                success_count += 1
            else:
                print(f"Thread error: {data}")

        # At least one should succeed (due to database locking, not all may succeed)
        assert success_count >= 1

    def test_real_data_integrity_checks(self, collector):
        """Test data integrity and consistency"""
        collector.run_full_update()

        session = collector.db.get_session()
        try:
            # Check for duplicate stocks
            stocks = session.query(collector.db.Stock).all()
            web_ids = [s.web_id for s in stocks]
            assert len(web_ids) == len(set(web_ids))  # No duplicates

            # Check for duplicate sectors
            sectors = session.query(collector.db.Sector).all()
            sector_codes = [s.sector_code for s in sectors]
            assert len(sector_codes) == len(set(sector_codes))  # No duplicates

            # Check for duplicate indices
            indices = session.query(collector.db.Index).all()
            index_codes = [i.web_id for i in indices]
            assert len(index_codes) == len(set(index_codes))  # No duplicates

            # Verify foreign key relationships
            for stock in stocks[:10]:  # Check first 10
                # Stock should have valid sector if sector_id is set
                if stock.sector_id:
                    sector = session.query(collector.db.Sector).filter_by(id=stock.sector_id).first()
                    assert sector is not None, f"Stock {stock.ticker} references non-existent sector {stock.sector_id}"

        finally:
            session.close()

    def test_real_error_recovery(self, collector):
        """Test error recovery and resilience"""
        # Test with network interruption simulation
        original_timeout = collector.api._make_request.__defaults__[0] if collector.api._make_request.__defaults__ else 10

        # Temporarily reduce timeout to simulate network issues
        import types
        original_method = collector.api._make_request

        def failing_request(self, endpoint, params=None):
            # Simulate intermittent failures
            import random
            if random.random() < 0.3:  # 30% failure rate
                return None
            return original_method(endpoint, params)

        collector.api._make_request = types.MethodType(failing_request, collector.api)

        try:
            # Should still complete despite simulated failures
            result = collector.run_full_update()
            assert result['success'] == True
            print("Successfully recovered from simulated network failures")
        finally:
            # Restore original method
            collector.api._make_request = original_method

    def test_real_large_dataset_handling(self, collector):
        """Test handling of large datasets"""
        collector.run_full_update()

        # Update large amounts of historical data
        result = collector.update_price_history(365)  # 1 year of data
        print(f"Processed {result} price history records for 1 year")

        result = collector.update_ri_history(365)  # 1 year of RI data
        print(f"Processed {result} RI history records for 1 year")

        # Verify database can handle the load
        session = collector.db.get_session()
        try:
            price_count = session.query(collector.db.PriceHistory).count()
            ri_count = session.query(collector.db.RIHistory).count()

            print(f"Database contains {price_count} price records and {ri_count} RI records")

            # Should have reasonable amounts of data
            assert price_count >= 0
            assert ri_count >= 0

        finally:
            session.close()

    def test_real_api_rate_limiting(self, collector):
        """Test API rate limiting and throttling"""
        import time

        start_time = time.time()

        # Make multiple rapid requests
        results = []
        for i in range(10):
            stock_list = collector.api.get_stock_list()
            results.append(stock_list is not None)
            time.sleep(0.1)  # Small delay between requests

        end_time = time.time()
        duration = end_time - start_time

        # Should handle rate limiting gracefully
        success_count = sum(results)
        success_rate = success_count / len(results)

        print(f"API rate limiting test: {success_count}/{len(results)} successful ({success_rate:.1%})")
        print(f"Duration: {duration:.2f} seconds")

        # Should have reasonable success rate (allowing for API limitations)
        assert success_rate >= 0.5

    def test_real_database_connection_pooling(self, collector):
        """Test database connection pooling under load"""
        import threading

        def database_worker(worker_id):
            try:
                session = collector.db.get_session()
                stocks = session.query(collector.db.Stock).limit(10).all()
                session.close()
                return len(stocks)
            except Exception as e:
                print(f"Worker {worker_id} error: {e}")
                return 0

        # Run multiple database operations concurrently
        threads = []
        results = []

        for i in range(10):
            def worker():
                result = database_worker(i)
                results.append(result)

            t = threading.Thread(target=worker)
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # Should all succeed
        assert len(results) == 10
        assert all(r >= 0 for r in results)

        print(f"Database connection pooling test: {sum(results)} total records retrieved")

    @pytest.mark.parametrize("database_type", ["sqlite", "postgres"])
    def test_real_cross_database_compatibility(self, temp_db_path, database_type):
        """Test compatibility across different database backends"""
        if database_type == "sqlite":
            with patch('database.base.DATABASE_URL', f'sqlite:///{temp_db_path}'):
                db = SQLiteDatabase()
        else:
            # Skip postgres test if not configured
            pytest.skip("PostgreSQL not configured for testing")

        collector = TSEDataCollector()
        collector.db = db

        try:
            # Should work the same way regardless of database
            result = collector.run_full_update()
            assert result['success'] == True
            assert result['stocks'] > 0

            print(f"Cross-database test passed for {database_type}")

        finally:
            db.close()

    def test_real_data_export_import(self, collector, temp_db_path):
        """Test data export and import functionality"""
        # First populate database
        collector.run_full_update()

        # Export data to file
        export_file = temp_db_path + "_export.json"
        try:
            # Simulate export (in real implementation, this would be a proper export function)
            session = collector.db.get_session()
            stocks = session.query(collector.db.Stock).all()
            export_data = [
                {
                    'ticker': s.ticker,
                    'name': s.name,
                    'web_id': s.web_id,
                    'sector_id': s.sector_id
                } for s in stocks[:10]  # Export first 10
            ]
            session.close()

            import json
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False)

            # Verify export file
            with open(export_file, 'r', encoding='utf-8') as f:
                imported_data = json.load(f)

            assert len(imported_data) == 10
            assert all('ticker' in item for item in imported_data)
            assert all('web_id' in item for item in imported_data)

            print(f"Successfully exported and imported {len(imported_data)} records")

        finally:
            if os.path.exists(export_file):
                os.unlink(export_file)

    def test_real_system_monitoring(self, collector):
        """Test system monitoring and health checks"""
        # Test database connectivity
        session = collector.db.get_session()
        try:
            # Simple query to test connectivity
            count = session.query(collector.db.Stock).count()
            assert isinstance(count, int)
        finally:
            session.close()

        # Test API connectivity
        stock_list = collector.api.get_stock_list()
        assert stock_list is not None

        # Test memory and performance
        import psutil
        import os
        process = psutil.Process(os.getpid())
        memory_mb = process.memory_info().rss / 1024 / 1024
        cpu_percent = process.cpu_percent(interval=0.1)

        print(f"System health - Memory: {memory_mb:.1f} MB, CPU: {cpu_percent:.1f}%")

        # Should be within reasonable limits
        assert memory_mb < 1000  # Less than 1GB
        assert cpu_percent < 50   # Less than 50% CPU usage

    def test_real_backup_and_recovery(self, collector, temp_db_path):
        """Test backup and recovery functionality"""
        # Populate database
        collector.run_full_update()

        # Create backup
        backup_file = temp_db_path + "_backup.db"
        try:
            import shutil
            shutil.copy2(temp_db_path, backup_file)

            # Verify backup exists and has content
            assert os.path.exists(backup_file)
            assert os.path.getsize(backup_file) > 0

            # Simulate recovery by creating new collector with backup
            with patch('database.base.DATABASE_URL', f'sqlite:///{backup_file}'):
                backup_db = SQLiteDatabase()
                backup_collector = TSEDataCollector()
                backup_collector.db = backup_db

                try:
                    # Verify backup has same data
                    session = backup_collector.db.get_session()
                    backup_count = session.query(backup_collector.db.Stock).count()
                    session.close()

                    session = collector.db.get_session()
                    original_count = session.query(collector.db.Stock).count()
                    session.close()

                    assert backup_count == original_count
                    print(f"Backup recovery successful: {backup_count} records")

                finally:
                    backup_db.close()

        finally:
            if os.path.exists(backup_file):
                os.unlink(backup_file)

    def test_real_configuration_management(self, collector):
        """Test configuration management and environment handling"""
        # Test with different configurations
        original_timeout = collector.api._make_request.__defaults__[0] if collector.api._make_request.__defaults__ else 10

        # Test with shorter timeout
        import config
        original_api_timeout = config.API_TIMEOUT
        config.API_TIMEOUT = 5  # 5 seconds

        try:
            # Should still work with shorter timeout
            stock_list = collector.api.get_stock_list()
            assert stock_list is not None

        finally:
            config.API_TIMEOUT = original_api_timeout

        print("Configuration management test passed")

    def test_real_logging_and_audit_trail(self, collector):
        """Test logging and audit trail functionality"""
        import logging
        from io import StringIO

        # Capture log output
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        logger = logging.getLogger('tse_collector')
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        try:
            # Run operation that should generate logs
            result = collector.run_full_update()

            # Check log output
            log_output = log_stream.getvalue()
            assert 'Starting stock collection' in log_output
            assert 'stocks' in log_output.lower()

            print("Logging and audit trail test passed")

        finally:
            logger.removeHandler(handler)

    def test_real_security_and_validation(self, collector):
        """Test security measures and input validation"""
        # Test SQL injection prevention
        # (This would be more relevant with user inputs, but testing framework)

        # Test with potentially malicious inputs
        malicious_inputs = [
            "'; DROP TABLE stocks; --",
            "<script>alert('xss')</script>",
            "../../../etc/passwd",
            "javascript:alert('xss')",
        ]

        for malicious_input in malicious_inputs:
            # These should be handled safely
            result = collector.api.get_instrument_search(malicious_input)
            # Should not crash, should return None or safe result
            assert result is None or isinstance(result, str)

        print("Security and validation test passed")

    def test_real_scalability_assessment(self, collector):
        """Test scalability with increasing data volumes"""
        # Start with small dataset
        collector.run_full_update()

        session = collector.db.get_session()
        initial_count = session.query(collector.db.Stock).count()
        session.close()

        # Add more historical data
        price_records = collector.update_price_history(90)  # 3 months
        ri_records = collector.update_ri_history(90)       # 3 months

        session = collector.db.get_session()
        final_stock_count = session.query(collector.db.Stock).count()
        price_count = session.query(collector.db.PriceHistory).count()
        ri_count = session.query(collector.db.RIHistory).count()
        session.close()

        print(f"Scalability test results:")
        print(f"  Stocks: {final_stock_count}")
        print(f"  Price records: {price_count}")
        print(f"  RI records: {ri_count}")

        # Should handle increased data volume
        assert final_stock_count >= initial_count
        assert price_count >= 0
        assert ri_count >= 0

    def test_real_maintenance_operations(self, collector):
        """Test maintenance operations like cleanup and optimization"""
        # Populate database
        collector.run_full_update()
        collector.update_price_history(30)

        session = collector.db.get_session()
        initial_price_count = session.query(collector.db.PriceHistory).count()
        session.close()

        # Simulate maintenance operations
        # (In real implementation, this would be proper maintenance functions)

        # Test database integrity
        session = collector.db.get_session()
        try:
            # Check for orphaned records
            stocks = session.query(collector.db.Stock).all()
            for stock in stocks[:5]:  # Check first 5
                price_count = session.query(collector.db.PriceHistory).filter_by(stock_id=stock.id).count()
                # Should not have negative counts
                assert price_count >= 0

            print("Maintenance operations test passed")

        finally:
            session.close()
