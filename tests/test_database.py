import pytest
import tempfile
import os
from datetime import date
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.sqlite_db import SQLiteDatabase
from database.models import Stock, Sector, Index, PriceHistory, RIHistory


class TestSQLiteDatabase:
    @pytest.fixture
    def temp_db_path(self):
        # Create a temporary database file
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        yield path
        # Cleanup
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def temp_db(self, temp_db_path):
        with patch('database.base.DATABASE_URL', f'sqlite:///{temp_db_path}'):
            db = SQLiteDatabase()
            yield db
            # Properly close database connections
            db.close()

    def test_init(self, temp_db):
        assert temp_db.engine is not None
        assert temp_db.SessionLocal is not None

    def test_add_stock_new(self, temp_db):
        stock_data = {
            'ticker': 'ABC',
            'name': 'شرکت نمونه',
            'web_id': '123456',
            'market': 'بازار اول'
        }

        result = temp_db.add_stock(stock_data)
        assert result is not None
        assert result.ticker == 'ABC'
        assert result.name == 'شرکت نمونه'
        assert result.web_id == '123456'

    def test_add_stock_duplicate(self, temp_db):
        stock_data = {
            'ticker': 'ABC',
            'name': 'شرکت نمونه',
            'web_id': '123456',
            'market': 'بازار اول'
        }

        # Add first time
        result1 = temp_db.add_stock(stock_data)
        # Add second time (should return existing)
        result2 = temp_db.add_stock(stock_data)

        assert result1 is not None
        assert result2 is not None
        assert result1.id == result2.id

    def test_get_stock_by_ticker(self, temp_db):
        stock_data = {
            'ticker': 'ABC',
            'name': 'شرکت نمونه',
            'web_id': '123456',
            'market': 'بازار اول'
        }

        temp_db.add_stock(stock_data)
        result = temp_db.get_stock_by_ticker('ABC')

        assert result is not None
        assert result.ticker == 'ABC'
        assert result.name == 'شرکت نمونه'

    def test_get_stock_by_ticker_not_found(self, temp_db):
        result = temp_db.get_stock_by_ticker('NONEXISTENT')
        assert result is None

    def test_get_stock_by_web_id(self, temp_db):
        stock_data = {
            'ticker': 'ABC',
            'name': 'شرکت نمونه',
            'web_id': '123456',
            'market': 'بازار اول'
        }

        temp_db.add_stock(stock_data)
        result = temp_db.get_stock_by_web_id('123456')

        assert result is not None
        assert result.web_id == '123456'
        assert result.ticker == 'ABC'

    def test_get_stock_by_web_id_not_found(self, temp_db):
        result = temp_db.get_stock_by_web_id('NONEXISTENT')
        assert result is None

    def test_add_index_new(self, temp_db):
        index_data = {
            'name': 'شاخص کل',
            'web_id': '123456'
        }

        result = temp_db.add_index(index_data)
        assert result is not None
        assert result.name == 'شاخص کل'
        assert result.web_id == '123456'

    def test_add_index_duplicate(self, temp_db):
        index_data = {
            'name': 'شاخص کل',
            'web_id': '123456'
        }

        # Add first time
        result1 = temp_db.add_index(index_data)
        # Add second time (should return existing)
        result2 = temp_db.add_index(index_data)

        assert result1 is not None
        assert result2 is not None
        assert result1.id == result2.id

    def test_add_price_history(self, temp_db):
        # First add a stock
        stock_data = {
            'ticker': 'ABC',
            'name': 'شرکت نمونه',
            'web_id': '123456',
            'market': 'بازار اول'
        }
        stock = temp_db.add_stock(stock_data)

        price_data = [{
            'stock_id': stock.id,
            'j_date': '1402/01/01',
            'date': date(2023, 3, 21),
            'open_price': 1000,
            'high_price': 1100,
            'low_price': 900,
            'close_price': 1050,
            'volume': 1000000,
            'value': 1000000000,
            'num_trades': 1000
        }]

        count = temp_db.add_price_history(price_data)
        assert count == 1

    def test_add_price_history_empty(self, temp_db):
        count = temp_db.add_price_history([])
        assert count == 0

    def test_add_ri_history(self, temp_db):
        # First add a stock
        stock_data = {
            'ticker': 'ABC',
            'name': 'شرکت نمونه',
            'web_id': '123456',
            'market': 'بازار اول'
        }
        stock = temp_db.add_stock(stock_data)

        ri_data = [{
            'stock_id': stock.id,
            'j_date': '1402/01/01',
            'date': date(2023, 3, 21),
            'vol_buy_r': 500000,
            'vol_sell_r': 300000,
            'val_buy_r': 500000000,
            'val_sell_r': 300000000,
            'vol_buy_i': 500000,
            'vol_sell_i': 700000,
            'val_buy_i': 500000000,
            'val_sell_i': 700000000
        }]

        count = temp_db.add_ri_history(ri_data)
        assert count == 1

    def test_get_last_price_date(self, temp_db):
        # First add a stock
        stock_data = {
            'ticker': 'ABC',
            'name': 'شرکت نمونه',
            'web_id': '123456',
            'market': 'بازار اول'
        }
        stock = temp_db.add_stock(stock_data)

        # Add price history
        price_data = [{
            'stock_id': stock.id,
            'j_date': '1402/01/01',
            'date': date(2023, 3, 21),
            'open_price': 1000,
            'close_price': 1050,
            'volume': 1000000,
            'value': 1000000000,
            'num_trades': 1000
        }]
        temp_db.add_price_history(price_data)

        last_date = temp_db.get_last_price_date(stock.id)
        assert last_date == '1402/01/01'

    def test_get_last_price_date_no_data(self, temp_db):
        # First add a stock
        stock_data = {
            'ticker': 'ABC',
            'name': 'شرکت نمونه',
            'web_id': '123456',
            'market': 'بازار اول'
        }
        stock = temp_db.add_stock(stock_data)

        last_date = temp_db.get_last_price_date(stock.id)
        assert last_date is None

    def test_get_last_ri_date(self, temp_db):
        # First add a stock
        stock_data = {
            'ticker': 'ABC',
            'name': 'شرکت نمونه',
            'web_id': '123456',
            'market': 'بازار اول'
        }
        stock = temp_db.add_stock(stock_data)

        # Add RI history
        ri_data = [{
            'stock_id': stock.id,
            'j_date': '1402/01/01',
            'date': date(2023, 3, 21),
            'vol_buy_r': 500000,
            'vol_sell_r': 300000,
            'val_buy_r': 500000000,
            'val_sell_r': 300000000,
            'vol_buy_i': 500000,
            'vol_sell_i': 700000,
            'val_buy_i': 500000000,
            'val_sell_i': 700000000
        }]
        temp_db.add_ri_history(ri_data)

        last_date = temp_db.get_last_ri_date(stock.id)
        assert last_date == '1402/01/01'

    def test_get_last_ri_date_no_data(self, temp_db):
        # First add a stock
        stock_data = {
            'ticker': 'ABC',
            'name': 'شرکت نمونه',
            'web_id': '123456',
            'market': 'بازار اول'
        }
        stock = temp_db.add_stock(stock_data)

        last_date = temp_db.get_last_ri_date(stock.id)
        assert last_date is None

    def test_get_sector_by_code(self, temp_db):
        # Test the get_sector_by_code method
        result = temp_db.get_sector_by_code(1.0)
        assert result is None  # No sectors in empty database

    def test_add_index_history(self, temp_db):
        # First add an index
        index_data = {
            'name': 'شاخص کل',
            'web_id': '123456'
        }
        index = temp_db.add_index(index_data)

        index_history_data = [{
            'index_id': index.id,
            'j_date': '1402/01/01',
            'date': date(2023, 3, 21),
            'value': 1000000.0,
            'change_percent': 0.1,
            'open_price': 990000.0,
            'high_price': 1010000.0,
            'low_price': 980000.0,
            'close_price': 1000000.0,
            'adj_close': 1000000.0
        }]

        count = temp_db.add_index_history(index_history_data)
        assert count == 1

    def test_add_sector_index_history(self, temp_db):
        sector_index_history_data = [{
            'sector_id': 1,
            'j_date': '1402/01/01',
            'date': date(2023, 3, 21),
            'open_price': 990000.0,
            'high_price': 1010000.0,
            'low_price': 980000.0,
            'close_price': 1000000.0,
            'adj_close': 1000000.0,
            'volume': 1000000
        }]

        count = temp_db.add_sector_index_history(sector_index_history_data)
        assert count == 1

    def test_add_shareholder(self, temp_db):
        shareholder_data = {
            'shareholder_id': '123456789',
            'name': 'سهامدار نمونه',
            'is_individual': True
        }

        result = temp_db.add_shareholder(shareholder_data)
        assert result is not None
        assert result.shareholder_id == '123456789'
        assert result.name == 'سهامدار نمونه'

    def test_get_shareholder_by_id(self, temp_db):
        shareholder_data = {
            'shareholder_id': '123456789',
            'name': 'سهامدار نمونه',
            'is_individual': True
        }

        temp_db.add_shareholder(shareholder_data)
        result = temp_db.get_shareholder_by_id('123456789')

        assert result is not None
        assert result.shareholder_id == '123456789'
        assert result.name == 'سهامدار نمونه'

    def test_add_major_shareholder_history(self, temp_db):
        # First add a stock and shareholder
        stock_data = {
            'ticker': 'ABC',
            'name': 'شرکت نمونه',
            'web_id': '123456',
            'market': 'بازار اول'
        }
        stock = temp_db.add_stock(stock_data)

        shareholder_data = {
            'shareholder_id': '123456789',
            'name': 'سهامدار نمونه',
            'is_individual': True
        }
        shareholder = temp_db.add_shareholder(shareholder_data)

        history_data = [{
            'stock_id': stock.id,
            'shareholder_id': shareholder.shareholder_id,
            'j_date': '1402/01/01',
            'date': date(2023, 3, 21),
            'shares_count': 1000000,
            'percentage': 10.5
        }]

        count = temp_db.add_major_shareholder_history(history_data)
        assert count == 1

    def test_add_intraday_trades(self, temp_db):
        # First add a stock
        stock_data = {
            'ticker': 'ABC',
            'name': 'شرکت نمونه',
            'web_id': '123456',
            'market': 'بازار اول'
        }
        stock = temp_db.add_stock(stock_data)

        trades_data = [{
            'stock_id': stock.id,
            'j_date': '1402/01/01',
            'date': date(2023, 3, 21),
            'time': '09:00:00',
            'price': 1000.0,
            'volume': 10000,
            'value': 10000000
        }]

        count = temp_db.add_intraday_trades(trades_data)
        assert count == 1

    def test_add_usd_history(self, temp_db):
        usd_history_data = [{
            'j_date': '1402/01/01',
            'date': date(2023, 3, 21),
            'open_price': 49000.0,
            'high_price': 51000.0,
            'low_price': 48000.0,
            'close_price': 50000.0,
            'adj_close': 50000.0,
            'volume': 1000000
        }]

        count = temp_db.add_usd_history(usd_history_data)
        assert count == 1

    def test_get_last_index_date(self, temp_db):
        # First add an index
        index_data = {
            'name': 'شاخص کل',
            'web_id': '123456'
        }
        index = temp_db.add_index(index_data)

        # Add index history
        index_history_data = [{
            'index_id': index.id,
            'j_date': '1402/01/01',
            'date': date(2023, 3, 21),
            'open_price': 990000.0,
            'high_price': 1010000.0,
            'low_price': 980000.0,
            'close_price': 1000000.0,
            'adj_close': 1000000.0
        }]
        temp_db.add_index_history(index_history_data)

        last_date = temp_db.get_last_index_date(index.id)
        assert last_date == '1402/01/01'

    def test_get_last_sector_index_date(self, temp_db):
        # Add sector index history
        sector_index_history_data = [{
            'sector_id': 1,
            'j_date': '1402/01/01',
            'date': date(2023, 3, 21),
            'open_price': 990000.0,
            'high_price': 1010000.0,
            'low_price': 980000.0,
            'close_price': 1000000.0,
            'adj_close': 1000000.0,
            'volume': 1000000
        }]
        temp_db.add_sector_index_history(sector_index_history_data)

        last_date = temp_db.get_last_sector_index_date(1)
        assert last_date == '1402/01/01'

    def test_get_last_shareholder_date(self, temp_db):
        # First add a stock
        stock_data = {
            'ticker': 'ABC',
            'name': 'شرکت نمونه',
            'web_id': '123456',
            'market': 'بازار اول'
        }
        stock = temp_db.add_stock(stock_data)

        # Add shareholder history
        shareholder_data = {
            'shareholder_id': '123456789',
            'name': 'سهامدار نمونه',
            'is_individual': True
        }
        shareholder = temp_db.add_shareholder(shareholder_data)

        history_data = [{
            'stock_id': stock.id,
            'shareholder_id': shareholder.shareholder_id,
            'j_date': '1402/01/01',
            'date': date(2023, 3, 21),
            'shares_count': 1000000,
            'percentage': 10.5
        }]
        temp_db.add_major_shareholder_history(history_data)

        last_date = temp_db.get_last_shareholder_date(stock.id)
        assert last_date == '1402/01/01'

    def test_get_last_usd_date(self, temp_db):
        # Add USD history
        usd_history_data = [{
            'j_date': '1402/01/01',
            'date': date(2023, 3, 21),
            'open_price': 49000.0,
            'high_price': 51000.0,
            'low_price': 48000.0,
            'close_price': 50000.0,
            'adj_close': 50000.0,
            'volume': 1000000
        }]
        temp_db.add_usd_history(usd_history_data)

        last_date = temp_db.get_last_usd_date()
        assert last_date == '1402/01/01'

    def test_add_stock_exception_handling(self, temp_db):
        stock_data = {
            'ticker': 'ABC',
            'name': 'شرکت نمونه',
            'web_id': '123456',
            'market': 'بازار اول'
        }

        # Mock session.commit to raise an exception
        with patch.object(temp_db, 'get_session') as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = None
            mock_session.commit.side_effect = Exception("Database error")

            result = temp_db.add_stock(stock_data)
            assert result is None
            mock_session.rollback.assert_called_once()

    def test_add_index_exception_handling(self, temp_db):
        index_data = {
            'name': 'شاخص کل',
            'web_id': '123456'
        }

        # Mock session.commit to raise an exception
        with patch.object(temp_db, 'get_session') as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = None
            mock_session.commit.side_effect = Exception("Database error")

            result = temp_db.add_index(index_data)
            assert result is None
            mock_session.rollback.assert_called_once()

    def test_add_shareholder_exception_handling(self, temp_db):
        shareholder_data = {
            'shareholder_id': '123456789',
            'name': 'سهامدار نمونه',
            'is_individual': True
        }

        # Mock session.commit to raise an exception
        with patch.object(temp_db, 'get_session') as mock_get_session:
            mock_session = MagicMock()
            mock_get_session.return_value = mock_session
            mock_session.query.return_value.filter.return_value.first.return_value = None
            mock_session.commit.side_effect = Exception("Database error")

            result = temp_db.add_shareholder(shareholder_data)
            assert result is None
            mock_session.rollback.assert_called_once()
