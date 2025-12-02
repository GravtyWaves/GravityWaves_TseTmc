"""
Tests for PostgreSQL database implementation
"""

import pytest
from unittest.mock import MagicMock, patch, Mock
from database.postgres_db import PostgreSQLDatabase
from database.models import Stock, PriceHistory, RIHistory, Index, IndexHistory, Sector, SectorIndexHistory, Shareholder, MajorShareholderHistory, IntradayTrade, USDHistory


class TestPostgreSQLDatabase:
    """Test PostgreSQL database operations"""

    def setup_method(self, method):
        """Setup test instance"""
        with patch('database.postgres_db.DatabaseBase.__init__') as mock_init:
            mock_init.return_value = None
            self.db = PostgreSQLDatabase()

    @patch('database.postgres_db.DatabaseBase.get_session')
    def test_add_stock_success(self, mock_get_session):
        """Test adding new stock successfully"""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        # Mock no existing stock
        mock_session.query.return_value.filter.return_value.first.return_value = None

        stock_data = {
            'ticker': 'TEST',
            'name': 'Test Stock',
            'web_id': '12345'
        }

        result = self.db.add_stock(stock_data)

        assert result is not None
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()
        mock_session.expunge.assert_called_once()
        mock_session.close.assert_called_once()

    @patch('database.postgres_db.DatabaseBase.get_session')
    def test_add_stock_existing(self, mock_get_session):
        """Test adding existing stock returns None"""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        # Mock existing stock
        existing_stock = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = existing_stock

        stock_data = {
            'ticker': 'TEST',
            'name': 'Test Stock'
        }

        result = self.db.add_stock(stock_data)

        assert result is None
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()
        mock_session.close.assert_called_once()

    @patch('database.postgres_db.DatabaseBase.get_session')
    def test_add_stock_exception(self, mock_get_session):
        """Test handling exception during stock addition"""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_session.query.return_value.filter.return_value.first.side_effect = Exception("DB error")

        stock_data = {'ticker': 'TEST'}

        result = self.db.add_stock(stock_data)

        assert result is None
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()

    @patch('database.postgres_db.DatabaseBase.get_session')
    def test_get_stock_by_ticker(self, mock_get_session):
        """Test getting stock by ticker"""
        mock_session = MagicMock()
        mock_stock = MagicMock()
        mock_get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = mock_stock

        result = self.db.get_stock_by_ticker('TEST')

        assert result == mock_stock
        mock_session.close.assert_called_once()

    @patch('database.postgres_db.DatabaseBase.get_session')
    def test_get_stock_by_web_id(self, mock_get_session):
        """Test getting stock by web_id"""
        mock_session = MagicMock()
        mock_stock = MagicMock()
        mock_get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = mock_stock

        result = self.db.get_stock_by_web_id('12345')

        assert result == mock_stock
        mock_session.close.assert_called_once()

    @patch('database.postgres_db.DatabaseBase.get_session')
    def test_get_sector_by_code(self, mock_get_session):
        """Test getting sector by code"""
        mock_session = MagicMock()
        mock_sector = MagicMock()
        mock_get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = mock_sector

        result = self.db.get_sector_by_code(1.0)

        assert result == mock_sector
        mock_session.close.assert_called_once()

    @patch('database.postgres_db.DatabaseBase.batch_insert')
    def test_add_price_history(self, mock_batch_insert):
        """Test adding price history"""
        mock_batch_insert.return_value = 5

        history_data = [{'date': '2023-01-01', 'price': 100}]
        result = self.db.add_price_history(history_data)

        assert result == 5
        mock_batch_insert.assert_called_once_with(PriceHistory, history_data)

    @patch('database.postgres_db.DatabaseBase.batch_insert')
    def test_add_ri_history(self, mock_batch_insert):
        """Test adding RI history"""
        mock_batch_insert.return_value = 3

        history_data = [{'date': '2023-01-01', 'ri_value': 50}]
        result = self.db.add_ri_history(history_data)

        assert result == 3
        mock_batch_insert.assert_called_once_with(RIHistory, history_data)

    @patch('database.postgres_db.DatabaseBase.get_session')
    def test_add_index_success(self, mock_get_session):
        """Test adding new index successfully"""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        # Mock no existing index
        mock_session.query.return_value.filter.return_value.first.return_value = None

        index_data = {
            'name': 'Test Index',
            'web_id': 'TEST'
        }

        result = self.db.add_index(index_data)

        assert result is not None
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()
        mock_session.expunge.assert_called_once()
        mock_session.close.assert_called_once()

    @patch('database.postgres_db.DatabaseBase.get_session')
    def test_add_index_existing(self, mock_get_session):
        """Test adding existing index returns existing"""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        # Mock existing index
        existing_index = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = existing_index

        index_data = {'name': 'Test Index'}

        result = self.db.add_index(index_data)

        assert result == existing_index
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()
        mock_session.close.assert_called_once()

    @patch('database.postgres_db.DatabaseBase.batch_insert')
    def test_add_index_history(self, mock_batch_insert):
        """Test adding index history"""
        mock_batch_insert.return_value = 10

        history_data = [{'date': '2023-01-01', 'value': 1000}]
        result = self.db.add_index_history(history_data)

        assert result == 10
        mock_batch_insert.assert_called_once_with(IndexHistory, history_data)

    @patch('database.postgres_db.DatabaseBase.batch_insert')
    def test_add_sector_index_history(self, mock_batch_insert):
        """Test adding sector index history"""
        mock_batch_insert.return_value = 7

        history_data = [{'date': '2023-01-01', 'sector_value': 500}]
        result = self.db.add_sector_index_history(history_data)

        assert result == 7
        mock_batch_insert.assert_called_once_with(SectorIndexHistory, history_data)

    @patch('database.postgres_db.DatabaseBase.get_session')
    def test_add_shareholder_success(self, mock_get_session):
        """Test adding new shareholder successfully"""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        # Mock no existing shareholder
        mock_session.query.return_value.filter.return_value.first.return_value = None

        shareholder_data = {
            'shareholder_id': '123',
            'name': 'Test Shareholder'
        }

        result = self.db.add_shareholder(shareholder_data)

        assert result is not None
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()
        mock_session.expunge.assert_called_once()
        mock_session.close.assert_called_once()

    @patch('database.postgres_db.DatabaseBase.get_session')
    def test_add_shareholder_existing(self, mock_get_session):
        """Test adding existing shareholder returns existing"""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        # Mock existing shareholder
        existing_shareholder = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = existing_shareholder

        shareholder_data = {'shareholder_id': '123'}

        result = self.db.add_shareholder(shareholder_data)

        assert result == existing_shareholder
        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()
        mock_session.close.assert_called_once()

    @patch('database.postgres_db.DatabaseBase.get_session')
    def test_get_shareholder_by_id(self, mock_get_session):
        """Test getting shareholder by id"""
        mock_session = MagicMock()
        mock_shareholder = MagicMock()
        mock_get_session.return_value = mock_session
        mock_session.query.return_value.filter.return_value.first.return_value = mock_shareholder

        result = self.db.get_shareholder_by_id('123')

        assert result == mock_shareholder
        mock_session.close.assert_called_once()

    @patch('database.postgres_db.DatabaseBase.batch_insert')
    def test_add_major_shareholder_history(self, mock_batch_insert):
        """Test adding major shareholder history"""
        mock_batch_insert.return_value = 4

        history_data = [{'date': '2023-01-01', 'shares': 1000}]
        result = self.db.add_major_shareholder_history(history_data)

        assert result == 4
        mock_batch_insert.assert_called_once_with(MajorShareholderHistory, history_data)

    @patch('database.postgres_db.DatabaseBase.batch_insert')
    def test_add_intraday_trades(self, mock_batch_insert):
        """Test adding intraday trades"""
        mock_batch_insert.return_value = 20

        trades_data = [{'time': '09:00', 'price': 100}]
        result = self.db.add_intraday_trades(trades_data)

        assert result == 20
        mock_batch_insert.assert_called_once_with(IntradayTrade, trades_data)

    @patch('database.postgres_db.DatabaseBase.batch_insert')
    def test_add_usd_history(self, mock_batch_insert):
        """Test adding USD history"""
        mock_batch_insert.return_value = 30

        history_data = [{'date': '2023-01-01', 'rate': 50000}]
        result = self.db.add_usd_history(history_data)

        assert result == 30
        mock_batch_insert.assert_called_once_with(USDHistory, history_data)

    @patch('database.postgres_db.DatabaseBase.get_session')
    def test_get_last_price_date(self, mock_get_session):
        """Test getting last price date"""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        # Mock query result
        mock_result = ('1402-01-01',)
        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_result

        result = self.db.get_last_price_date(1)

        assert result == '1402-01-01'
        mock_session.close.assert_called_once()

    @patch('database.postgres_db.DatabaseBase.get_session')
    def test_get_last_price_date_none(self, mock_get_session):
        """Test getting last price date when none exists"""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = None

        result = self.db.get_last_price_date(1)

        assert result is None
        mock_session.close.assert_called_once()

    @patch('database.postgres_db.DatabaseBase.get_session')
    def test_get_last_ri_date(self, mock_get_session):
        """Test getting last RI date"""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_result = ('1402-01-01',)
        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_result

        result = self.db.get_last_ri_date(1)

        assert result == '1402-01-01'
        mock_session.close.assert_called_once()

    @patch('database.postgres_db.DatabaseBase.get_session')
    def test_get_last_index_date(self, mock_get_session):
        """Test getting last index date"""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_result = ('1402-01-01',)
        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_result

        result = self.db.get_last_index_date(1)

        assert result == '1402-01-01'
        mock_session.close.assert_called_once()

    @patch('database.postgres_db.DatabaseBase.get_session')
    def test_get_last_sector_index_date(self, mock_get_session):
        """Test getting last sector index date"""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_result = ('1402-01-01',)
        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_result

        result = self.db.get_last_sector_index_date(1)

        assert result == '1402-01-01'
        mock_session.close.assert_called_once()

    @patch('database.postgres_db.DatabaseBase.get_session')
    def test_get_last_shareholder_date(self, mock_get_session):
        """Test getting last shareholder date"""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_result = ('1402-01-01',)
        mock_session.query.return_value.filter.return_value.order_by.return_value.first.return_value = mock_result

        result = self.db.get_last_shareholder_date(1)

        assert result == '1402-01-01'
        mock_session.close.assert_called_once()

    @patch('database.postgres_db.DatabaseBase.get_session')
    def test_get_last_usd_date(self, mock_get_session):
        """Test getting last USD date"""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_result = ('1402-01-01',)
        mock_session.query.return_value.order_by.return_value.first.return_value = mock_result

        result = self.db.get_last_usd_date()

        assert result == '1402-01-01'
        mock_session.close.assert_called_once()

    @patch('database.postgres_db.DatabaseBase.get_session')
    def test_get_last_usd_date_none(self, mock_get_session):
        """Test getting last USD date when none exists"""
        mock_session = MagicMock()
        mock_get_session.return_value = mock_session

        mock_session.query.return_value.order_by.return_value.first.return_value = None

        result = self.db.get_last_usd_date()

        assert result is None
        mock_session.close.assert_called_once()