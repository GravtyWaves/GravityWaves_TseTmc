import pytest
from unittest.mock import patch, MagicMock
from main import TSEDataCollector


class TestTSEDataCollectorAdditional:
    @pytest.fixture
    def collector(self):
        with patch('main.SQLiteDatabase'):
            collector = TSEDataCollector()
            collector.api = MagicMock()  # Ensure api is a MagicMock for compatibility
            yield collector

    @patch('main.logger')
    def test_create_database_success(self, mock_logger, collector):
        collector.create_database()
        collector.db.create_tables.assert_called_once()
        mock_logger.info.assert_any_call("Creating database tables")
        mock_logger.info.assert_any_call("Database tables created successfully")

    @patch('main.logger')
    def test_load_initial_data_success(self, mock_logger, collector):
        collector.db.load_sectors_from_file.return_value = None
        result = collector.load_initial_data()
        assert result == True
        collector.db.load_sectors_from_file.assert_called_once()
        mock_logger.info.assert_any_call("Loading initial data")
        mock_logger.info.assert_any_call("Initial data loaded successfully")

    @patch('main.logger')
    def test_load_initial_data_failure(self, mock_logger, collector):
        collector.db.load_sectors_from_file.side_effect = Exception("Load error")
        result = collector.load_initial_data()
        assert result == False
        mock_logger.error.assert_called_once_with("Error loading initial data: Load error")

    @patch('main.logger')
    @patch('main.TSEDataCollector.collect_stocks')
    def test_rebuild_table_stocks_success(self, mock_collect_stocks, mock_logger, collector):
        from unittest.mock import MagicMock
        session_mock = MagicMock()
        collector.db.get_session.return_value = session_mock

        query_mock = MagicMock()
        query_mock.count.return_value = 0
        session_mock.query.return_value = query_mock

        # Mock the Base.__subclasses__ to return a mock class
        with patch('database.models.Base') as mock_base:
            mock_stock_class = MagicMock()
            mock_stock_class.__tablename__ = 'stocks'
            mock_base.__subclasses__ = MagicMock(return_value=[mock_stock_class])

            result = collector.rebuild_table('stocks')

            assert result == True
            session_mock.query.assert_called_once()
            session_mock.query().delete.assert_called_once()
            session_mock.commit.assert_called_once()
            mock_collect_stocks.assert_called_once()
            mock_logger.info.assert_any_call("Rebuilding table: stocks")
            mock_logger.info.assert_any_call("Table stocks cleared")
            mock_logger.info.assert_any_call("Table stocks rebuilt successfully")

    @patch('main.logger')
    def test_rebuild_table_not_found(self, mock_logger, collector):
        from unittest.mock import MagicMock
        session_mock = MagicMock()
        collector.db.get_session.return_value = session_mock

        # Mock the Base.__subclasses__ to return empty list
        with patch('database.models.Base') as mock_base:
            mock_base.__subclasses__ = MagicMock(return_value=[])

            result = collector.rebuild_table('nonexistent')

            assert result == False
            mock_logger.error.assert_called_once_with("Table nonexistent not found")

    @patch('main.logger')
    def test_rebuild_table_exception(self, mock_logger, collector):
        from unittest.mock import MagicMock
        session_mock = MagicMock()
        collector.db.get_session.return_value = session_mock
        session_mock.commit.side_effect = Exception("Commit error")

        query_mock = MagicMock()
        query_mock.count.return_value = 0
        session_mock.query.return_value = query_mock

        # Mock the Base.__subclasses__ to return a mock class
        with patch('database.models.Base') as mock_base:
            mock_stock_class = MagicMock()
            mock_stock_class.__tablename__ = 'stocks'
            mock_base.__subclasses__ = MagicMock(return_value=[mock_stock_class])

            result = collector.rebuild_table('stocks')

            assert result == False
            session_mock.rollback.assert_called_once()
            mock_logger.error.assert_called_once_with("Error rebuilding table stocks: Commit error")

    @patch('main.logger')
    def test_collect_stocks_success(self, mock_logger, collector):
        # Mock API response
        mock_stocks = [
            {'ticker': 'فولاد', 'name': 'فولاد مبارکه', 'web_id': '65883838195688438', 'SectorCode': 1},
            {'ticker': 'خودرو', 'name': 'ایران خودرو', 'web_id': '35425587644337450', 'SectorCode': 2}
        ]
        collector.api.get_stock_list.return_value = mock_stocks

        # Mock database
        collector.db.add_stock = MagicMock(return_value=True)

        result = collector.collect_stocks()

        assert result == 2
        collector.api.get_stock_list.assert_called_once()
        assert collector.db.add_stock.call_count == 2
        mock_logger.info.assert_any_call("Starting stock collection")
        mock_logger.info.assert_any_call("Collected 2 new stocks from API (total: 2)")

    @patch('main.logger')
    def test_collect_stocks_empty_response(self, mock_logger, collector):
        collector.api.get_stock_list.return_value = []

        result = collector.collect_stocks()

        assert result == 0
        mock_logger.warning.assert_called_once_with("No stocks fetched from API")

    @patch('main.logger')
    def test_collect_sectors_success(self, mock_logger, collector):
        # Mock API response
        mock_sectors = [
            {'SectorCode': '1', 'SectorName': 'فلزات اساسی', 'SectorNameEn': 'Basic Metals'},
            {'SectorCode': '2', 'SectorName': 'خودرو', 'SectorNameEn': 'Automotive'}
        ]
        collector.api.get_sector_list.return_value = mock_sectors
        collector.db.add_sector = MagicMock(return_value=True)

        result = collector.collect_sectors()

        assert result == 2
        collector.api.get_sector_list.assert_called_once()
        assert collector.db.add_sector.call_count == 2
        mock_logger.info.assert_any_call("Starting sector collection")
        mock_logger.info.assert_any_call("Collected 2 sectors from API")

    @patch('main.logger')
    def test_collect_sectors_invalid_code(self, mock_logger, collector):
        # Mock API response with invalid sector code
        mock_sectors = [
            {'SectorCode': 'invalid', 'SectorName': 'صنعت نامعتبر', 'SectorNameEn': 'Invalid Industry'}
        ]
        collector.api.get_sector_list.return_value = mock_sectors
        collector.db.add_sector = MagicMock(return_value=True)

        result = collector.collect_sectors()

        assert result == 1
        # Should handle invalid sector code gracefully

    @patch('main.logger')
    def test_collect_indices_success(self, mock_logger, collector):
        # Mock API response
        mock_indices = [
            {'name': 'شاخص کل', 'web_id': '32097828799138957'},
            {'name': 'شاخص هم وزن', 'web_id': '43685883382847264'}
        ]
        collector.api.get_index_list.return_value = mock_indices
        collector.db.add_index = MagicMock(return_value=True)

        result = collector.collect_indices()

        assert result == 2
        collector.api.get_index_list.assert_called_once()
        assert collector.db.add_index.call_count == 2
        mock_logger.info.assert_any_call("Starting index collection")
        mock_logger.info.assert_any_call("Collected 2 indices from API")

    @patch('main.logger')
    def test_update_price_history(self, mock_logger, collector):
        result = collector.update_price_history(30)

        assert result == 0  # Currently returns 0 as not fully implemented
        mock_logger.info.assert_called_once_with("Starting price history update for last 30 days")
        mock_logger.warning.assert_called_once_with("Price history update from scraping not fully implemented yet")

    @patch('main.logger')
    def test_update_ri_history(self, mock_logger, collector):
        result = collector.update_ri_history(30)

        assert result == 0  # Currently returns 0 as not fully implemented
        mock_logger.info.assert_called_once_with("Starting RI history update for last 30 days")
        mock_logger.warning.assert_called_once_with("RI history update from scraping not fully implemented yet")

    @patch('main.logger')
    @patch('main.time')
    def test_run_full_update(self, mock_time, mock_logger, collector):
        # Mock time for performance measurement
        mock_time.time.return_value = 1000.0

        # Mock all collection methods
        collector.collect_stocks = MagicMock(return_value=100)
        collector.collect_sectors = MagicMock(return_value=20)
        collector.collect_indices = MagicMock(return_value=5)
        collector.update_price_history = MagicMock(return_value=500)
        collector.update_ri_history = MagicMock(return_value=200)

        result = collector.run_full_update()

        expected_result = {
            'stocks': 100,
            'sectors': 20,
            'indices': 5,
            'price_history': 500,
            'ri_history': 200,
            'success': True
        }
        assert result == expected_result

        mock_logger.info.assert_any_call("Starting full data update")
        mock_logger.info.assert_any_call("Full update completed in 0.00s")

    @patch('main.logger')
    @patch('main.time')
    def test_run_continuous_update_keyboard_interrupt(self, mock_time, mock_logger, collector):
        # Mock time.sleep to raise KeyboardInterrupt on first call
        mock_time.sleep.side_effect = KeyboardInterrupt()

        collector.run_full_update = MagicMock()

        collector.run_continuous_update(60)

        # Should call run_full_update once before interrupt
        collector.run_full_update.assert_called_once()
        mock_logger.info.assert_any_call("Continuous update stopped by user")

    @patch('main.logger')
    @patch('main.time')
    def test_run_continuous_update_with_exception(self, mock_time, mock_logger, collector):
        # Mock run_full_update to raise exception, then KeyboardInterrupt
        collector.run_full_update = MagicMock(side_effect=[Exception("Update failed"), KeyboardInterrupt()])

        collector.run_continuous_update(60)

        # Should call run_full_update twice (once failed, once interrupted)
        assert collector.run_full_update.call_count == 2
        mock_logger.error.assert_called_once_with("Error in continuous update: Update failed")

    @patch('main.logger')
    def test_rebuild_table_sectors(self, mock_logger, collector):
        session_mock = MagicMock()
        collector.db.get_session.return_value = session_mock

        with patch('database.models.Base') as mock_base:
            mock_sector_class = MagicMock()
            mock_sector_class.__tablename__ = 'sectors'
            mock_base.__subclasses__ = MagicMock(return_value=[mock_sector_class])

            collector.collect_sectors = MagicMock()

            result = collector.rebuild_table('sectors')

            assert result == True
            collector.collect_sectors.assert_called_once()

    @patch('main.logger')
    def test_rebuild_table_indices(self, mock_logger, collector):
        session_mock = MagicMock()
        collector.db.get_session.return_value = session_mock

        with patch('database.models.Base') as mock_base:
            mock_index_class = MagicMock()
            mock_index_class.__tablename__ = 'indices'
            mock_base.__subclasses__ = MagicMock(return_value=[mock_index_class])

            collector.collect_indices = MagicMock()

            result = collector.rebuild_table('indices')

            assert result == True
            collector.collect_indices.assert_called_once()

    @patch('main.logger')
    def test_rebuild_table_price_history(self, mock_logger, collector):
        session_mock = MagicMock()
        collector.db.get_session.return_value = session_mock

        with patch('database.models.Base') as mock_base:
            mock_price_class = MagicMock()
            mock_price_class.__tablename__ = 'price_history'
            mock_base.__subclasses__ = MagicMock(return_value=[mock_price_class])

            collector.update_price_history = MagicMock()

            result = collector.rebuild_table('price_history')

            assert result == True
            collector.update_price_history.assert_called_once_with(365)

    @patch('main.logger')
    def test_rebuild_table_ri_history(self, mock_logger, collector):
        session_mock = MagicMock()
        collector.db.get_session.return_value = session_mock

        with patch('database.models.Base') as mock_base:
            mock_ri_class = MagicMock()
            mock_ri_class.__tablename__ = 'ri_history'
            mock_base.__subclasses__ = MagicMock(return_value=[mock_ri_class])

            collector.update_ri_history = MagicMock()

            result = collector.rebuild_table('ri_history')

            assert result == True
            collector.update_ri_history.assert_called_once_with(365)

    @patch('main.logger')
    def test_rebuild_table_unknown_table(self, mock_logger, collector):
        session_mock = MagicMock()
        collector.db.get_session.return_value = session_mock

        with patch('database.models.Base') as mock_base:
            mock_unknown_class = MagicMock()
            mock_unknown_class.__tablename__ = 'unknown_table'
            mock_base.__subclasses__ = MagicMock(return_value=[mock_unknown_class])

            result = collector.rebuild_table('unknown_table')

            assert result == True
            mock_logger.warning.assert_called_once_with("No specific collection method for table unknown_table")

    @patch('main.logger')
    def test_collect_stocks_database_error(self, mock_logger, collector):
        mock_stocks = [{'ticker': 'فولاد', 'name': 'فولاد مبارکه', 'web_id': '65883838195688438'}]
        collector.api.get_stock_list.return_value = mock_stocks

        # Mock database error - add_stock returns False
        collector.db.add_stock = MagicMock(return_value=False)

        result = collector.collect_stocks()

        # Should return 0 since no stocks were successfully added
        assert result == 0

    @patch('main.logger')
    def test_collect_sectors_database_error(self, mock_logger, collector):
        mock_sectors = [{'SectorCode': '1', 'SectorName': 'فلزات اساسی'}]
        collector.api.get_sector_list.return_value = mock_sectors

        # Mock database error - add_sector returns False
        collector.db.add_sector = MagicMock(return_value=False)

        result = collector.collect_sectors()

        assert result == 0  # No successful additions

    @patch('main.logger')
    def test_collect_indices_database_error(self, mock_logger, collector):
        mock_indices = [{'name': 'شاخص کل', 'web_id': '32097828799138957'}]
        collector.api.get_index_list.return_value = mock_indices

        # Mock database error - add_index returns False
        collector.db.add_index = MagicMock(return_value=False)

        result = collector.collect_indices()

        assert result == 0  # No successful additions

    @patch('main.argparse.ArgumentParser')
    @patch('main.TSEDataCollector')
    @patch('builtins.print')
    @patch('main.logger')
    def test_main_create_database(self, mock_logger, mock_print, mock_collector_class, mock_parser_class):
        # Mock command line args
        mock_args = MagicMock()
        mock_args.command = 'create-db'
        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = mock_args
        mock_parser_class.return_value = mock_parser

        # Mock collector
        mock_collector = MagicMock()
        mock_collector_class.return_value = mock_collector

        from main import main
        main()

        mock_print.assert_called_with("Database created successfully")

    @patch('main.argparse.ArgumentParser')
    @patch('main.TSEDataCollector')
    @patch('builtins.print')
    @patch('main.logger')
    def test_main_load_initial_data(self, mock_logger, mock_print, mock_collector_class, mock_parser_class):
        # Mock command line args
        mock_args = MagicMock()
        mock_args.command = 'load-initial-data'
        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = mock_args
        mock_parser_class.return_value = mock_parser

        # Mock collector
        mock_collector = MagicMock()
        mock_collector.load_initial_data.return_value = True
        mock_collector_class.return_value = mock_collector

        from main import main
        main()

        mock_print.assert_called_with("Initial data loaded successfully")

    @patch('main.argparse.ArgumentParser')
    @patch('main.TSEDataCollector')
    @patch('builtins.print')
    @patch('main.logger')
    def test_main_full_update(self, mock_logger, mock_print, mock_collector_class, mock_parser_class):
        # Mock command line args
        mock_args = MagicMock()
        mock_args.command = 'update'
        mock_args.mode = 'full'
        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = mock_args
        mock_parser_class.return_value = mock_parser

        # Mock collector
        mock_collector = MagicMock()
        mock_collector.run_full_update.return_value = {'success': True}
        mock_collector_class.return_value = mock_collector

        from main import main
        main()

        mock_print.assert_called_with("Update completed: {'success': True}")

    @patch('main.argparse.ArgumentParser')
    @patch('main.TSEDataCollector')
    @patch('main.logger')
    def test_main_continuous_update(self, mock_logger, mock_collector_class, mock_parser_class):
        # Mock command line args
        mock_args = MagicMock()
        mock_args.command = 'continuous-update'
        mock_args.interval = 60
        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = mock_args
        mock_parser_class.return_value = mock_parser

        # Mock collector
        mock_collector = MagicMock()
        mock_collector_class.return_value = mock_collector

        from main import main
        main()

        mock_collector.run_continuous_update.assert_called_once_with(60)

    @patch('main.argparse.ArgumentParser')
    @patch('main.logger')
    def test_main_invalid_command(self, mock_logger, mock_parser_class):
        # Mock command line args with invalid command
        mock_args = MagicMock()
        mock_args.command = 'invalid'
        mock_parser = MagicMock()
        mock_parser.parse_args.return_value = mock_args
        mock_parser_class.return_value = mock_parser

        from main import main
        main()

        mock_logger.error.assert_called_once_with("Unknown command: invalid")
