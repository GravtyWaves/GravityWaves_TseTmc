import pytest
from unittest.mock import patch, MagicMock, call
from main import TSEDataCollector, main
from database.sqlite_db import SQLiteDatabase
from api.tse_api import TSEAPIClient


class TestTSEDataCollector:
    @pytest.fixture
    def collector(self):
        with patch('main.SQLiteDatabase'), patch('main.TSEAPIClient'):
            collector = TSEDataCollector()
            yield collector

    def test_init(self, collector):
        assert collector.db is not None
        assert collector.api is not None

    @patch('main.logger')
    def test_collect_stocks_success(self, mock_logger, collector):
        # Mock API response
        mock_stock_list = [
            {'Symbol': 'ABC', 'CompanyName': 'شرکت نمونه', 'CompanyNameEn': 'Sample Company', 'InsCode': '123456', 'SectorCode': 1.0}
        ]
        collector.api.get_stock_list.return_value = mock_stock_list
        collector.db.add_stock.return_value = MagicMock()

        result = collector.collect_stocks()

        assert result == 1
        collector.api.get_stock_list.assert_called_once()
        collector.db.add_stock.assert_called_once()
        mock_logger.info.assert_any_call("Starting stock collection")
        mock_logger.info.assert_any_call("Collected 1 stocks")

    @patch('main.logger')
    def test_collect_stocks_api_failure(self, mock_logger, collector):
        collector.api.get_stock_list.return_value = None

        result = collector.collect_stocks()

        assert result == 0
        mock_logger.error.assert_called_once_with("Failed to fetch stock list")

    @patch('main.logger')
    def test_collect_stocks_db_error(self, mock_logger, collector):
        mock_stock_list = [
            {'Symbol': 'ABC', 'CompanyName': 'شرکت نمونه', 'CompanyNameEn': 'Sample Company', 'InsCode': '123456', 'SectorCode': 1.0}
        ]
        collector.api.get_stock_list.return_value = mock_stock_list
        collector.db.add_stock.return_value = None

        result = collector.collect_stocks()

        assert result == 0

    @patch('main.logger')
    def test_collect_sectors_success(self, mock_logger, collector):
        mock_sector_list = [
            {'SectorCode': 1.0, 'SectorName': 'صنعت نمونه', 'SectorNameEn': 'Sample Sector', 'NAICSCode': '123', 'NAICSName': 'Sample NAICS'}
        ]
        collector.api.get_sector_list.return_value = mock_sector_list

        # Mock database operations
        mock_session = MagicMock()
        collector.db.get_session.return_value = mock_session
        collector.db.get_sector_by_code.return_value = None

        result = collector.collect_sectors()

        assert result == 1
        mock_logger.info.assert_any_call("Starting sector collection")
        mock_logger.info.assert_any_call("Collected 1 sectors")

    @patch('main.logger')
    def test_collect_indices_success(self, mock_logger, collector):
        mock_index_list = [
            {'IndexName': 'شاخص کل', 'IndexNameEn': 'Total Index', 'InsCode': '123456'}
        ]
        collector.api.get_index_list.return_value = mock_index_list
        collector.db.add_index.return_value = MagicMock()

        result = collector.collect_indices()

        assert result == 1
        collector.api.get_index_list.assert_called_once()
        collector.db.add_index.assert_called_once()
        mock_logger.info.assert_any_call("Starting index collection")
        mock_logger.info.assert_any_call("Collected 1 indices")

    @patch('main.logger')
    @patch('main.time.time', side_effect=[0, 1.5])
    @patch('main.log_performance')
    def test_update_price_history_success(self, mock_log_performance, mock_time, mock_logger, collector):
        # Mock API
        collector.api.get_date_range.return_value = ('1402/01/01', '1402/01/31')
        collector.api.get_price_history.return_value = [
            {'DEven': '1402/01/01', 'PriceFirst': 1000, 'PriceMax': 1100, 'PriceMin': 900, 'PClosing': 1050, 'QTotTran5J': 1000000, 'QTotCap': 1000000000, 'ZTotTran': 1000}
        ]

        # Mock database
        mock_stock = MagicMock()
        mock_stock.id = 1
        mock_stock.web_id = '123456'
        mock_stock.ticker = 'ABC'
        mock_session = MagicMock()
        mock_session.query.return_value.all.return_value = [mock_stock]
        collector.db.get_session.return_value = mock_session
        collector.db.get_last_price_date.return_value = None
        collector.db.add_price_history.return_value = 1

        result = collector.update_price_history(30)

        assert result == 1
        mock_logger.info.assert_any_call("Starting price history update for last 30 days")
        mock_logger.info.assert_any_call("Updated 1 price history records")
        mock_log_performance.assert_called_once()

    @patch('main.logger')
    @patch('main.time.time', side_effect=[0, 1.5])
    @patch('main.log_performance')
    def test_update_ri_history_success(self, mock_log_performance, mock_time, mock_logger, collector):
        # Mock API
        collector.api.get_date_range.return_value = ('1402/01/01', '1402/01/31')
        collector.api.get_ri_history.return_value = [
            {'DEven': '1402/01/01', 'QTotTran5Buy_N': 500000, 'QTotTran5Sell_N': 300000, 'QTotCapBuy_N': 500000000, 'QTotCapSell_N': 300000000,
             'QTotTran5Buy_I': 500000, 'QTotTran5Sell_I': 700000, 'QTotCapBuy_I': 500000000, 'QTotCapSell_I': 700000000}
        ]

        # Mock database
        mock_stock = MagicMock()
        mock_stock.id = 1
        mock_stock.web_id = '123456'
        mock_stock.ticker = 'ABC'
        mock_session = MagicMock()
        mock_session.query.return_value.all.return_value = [mock_stock]
        collector.db.get_session.return_value = mock_session
        collector.db.get_last_ri_date.return_value = None
        collector.db.add_ri_history.return_value = 1

        result = collector.update_ri_history(30)

        assert result == 1
        mock_logger.info.assert_any_call("Starting RI history update for last 30 days")
        mock_logger.info.assert_any_call("Updated 1 RI history records")
        mock_log_performance.assert_called_once()

    @patch('main.logger')
    @patch('main.time.time', side_effect=[0, 2.5])
    @patch('main.log_performance')
    def test_run_full_update(self, mock_log_performance, mock_time, mock_logger, collector):
        # Mock all collection methods
        with patch.object(collector, 'collect_stocks', return_value=10), \
             patch.object(collector, 'collect_sectors', return_value=5), \
             patch.object(collector, 'collect_indices', return_value=3), \
             patch.object(collector, 'update_price_history', return_value=100), \
             patch.object(collector, 'update_ri_history', return_value=100):

            result = collector.run_full_update()

            assert result['stocks'] == 10
            assert result['sectors'] == 5
            assert result['indices'] == 3
            assert result['price_history'] == 100
            assert result['ri_history'] == 100
            assert result['success'] == True

            mock_logger.info.assert_any_call("Starting full data update")
            mock_logger.info.assert_any_call("Full update completed in 2.50s")
            mock_log_performance.assert_called_once()

    @patch('main.logger')
    @patch('main.time.sleep')
    @patch('main.UPDATE_INTERVAL', 1)
    def test_run_continuous_update(self, mock_sleep, mock_logger, collector):
        with patch.object(collector, 'run_full_update', side_effect=[None, KeyboardInterrupt]):
            collector.run_continuous_update(1)

            assert collector.run_full_update.call_count == 2
            mock_logger.info.assert_any_call("Starting continuous update with 1s interval")
            mock_logger.info.assert_any_call("Continuous update stopped by user")

    @patch('main.logger')
    @patch('main.time.sleep')
    def test_run_continuous_update_error(self, mock_sleep, mock_logger, collector):
        with patch.object(collector, 'run_full_update', side_effect=[Exception("Test error"), KeyboardInterrupt]):
            collector.run_continuous_update(1)

            mock_logger.error.assert_called_once_with("Error in continuous update: Test error")
            mock_sleep.assert_called_once_with(60)  # Error sleep


class TestMainFunction:
    @patch('main.argparse.ArgumentParser.parse_args')
    @patch('main.TSEDataCollector')
    @patch('builtins.print')
    def test_main_full_mode(self, mock_print, mock_collector_class, mock_parse_args):
        mock_args = MagicMock()
        mock_args.mode = 'full'
        mock_args.days = 30
        mock_args.interval = None
        mock_parse_args.return_value = mock_args

        mock_collector = MagicMock()
        mock_collector.run_full_update.return_value = {'success': True}
        mock_collector_class.return_value = mock_collector

        main()

        mock_collector.run_full_update.assert_called_once()
        mock_print.assert_called_once_with("Update completed: {'success': True}")

    @patch('main.argparse.ArgumentParser.parse_args')
    @patch('main.TSEDataCollector')
    @patch('builtins.print')
    def test_main_continuous_mode(self, mock_print, mock_collector_class, mock_parse_args):
        mock_args = MagicMock()
        mock_args.mode = 'continuous'
        mock_args.days = 30
        mock_args.interval = 60
        mock_parse_args.return_value = mock_args

        mock_collector = MagicMock()
        mock_collector_class.return_value = mock_collector

        main()

        mock_collector.run_continuous_update.assert_called_once_with(60)

    @patch('main.argparse.ArgumentParser.parse_args')
    @patch('main.TSEDataCollector')
    @patch('builtins.print')
    def test_main_stocks_mode(self, mock_print, mock_collector_class, mock_parse_args):
        mock_args = MagicMock()
        mock_args.mode = 'stocks'
        mock_args.days = 30
        mock_args.interval = None
        mock_parse_args.return_value = mock_args

        mock_collector = MagicMock()
        mock_collector.collect_stocks.return_value = 5
        mock_collector_class.return_value = mock_collector

        main()

        mock_collector.collect_stocks.assert_called_once()
        mock_print.assert_called_once_with("Collected 5 stocks")

    @patch('main.argparse.ArgumentParser.parse_args')
    @patch('main.TSEDataCollector')
    @patch('builtins.print')
    def test_main_prices_mode(self, mock_print, mock_collector_class, mock_parse_args):
        mock_args = MagicMock()
        mock_args.mode = 'prices'
        mock_args.days = 15
        mock_args.interval = None
        mock_parse_args.return_value = mock_args

        mock_collector = MagicMock()
        mock_collector.update_price_history.return_value = 50
        mock_collector_class.return_value = mock_collector

        main()

        mock_collector.update_price_history.assert_called_once_with(15)
        mock_print.assert_called_once_with("Updated 50 price records")

    @patch('main.argparse.ArgumentParser.parse_args')
    @patch('main.logger')
    @patch('main.sys.exit')
    def test_main_exception(self, mock_exit, mock_logger, mock_parse_args):
        mock_args = MagicMock()
        mock_args.mode = 'full'
        mock_args.days = 30
        mock_args.interval = None
        mock_parse_args.return_value = mock_args

        with patch('main.TSEDataCollector', side_effect=Exception("Test error")):
            main()

        mock_logger.error.assert_called_once_with("Application error: Test error")
        mock_exit.assert_called_once_with(1)
