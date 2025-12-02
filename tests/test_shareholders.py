"""
Tests for api/shareholders.py
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from api.shareholders import fetch_and_store_shareholders


class TestFetchAndStoreShareholders:
    """Tests for fetch_and_store_shareholders"""

    @patch('database.postgres_db.get_postgres_session')
    @patch('database.sqlite_db.get_sqlite_session')
    def test_fetch_and_store_shareholders_success(self, mock_sqlite_session, mock_postgres_session):
        """Test successful shareholder data fetching and storing"""
        # Mock sessions
        mock_sqlite = MagicMock()
        mock_postgres = MagicMock()
        mock_sqlite_session.return_value = mock_sqlite
        mock_postgres_session.return_value = mock_postgres

        result = fetch_and_store_shareholders('TEST')

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert result.iloc[0]['Ticker'] == 'TEST'
        assert result.iloc[0]['Name'] == 'Holder1'

        # Verify database operations
        mock_sqlite.bulk_save_objects.assert_called_once()
        mock_sqlite.commit.assert_called_once()
        mock_sqlite.close.assert_called_once()

        mock_postgres.bulk_save_objects.assert_called_once()
        mock_postgres.commit.assert_called_once()
        mock_postgres.close.assert_called_once()

    @patch('database.postgres_db.get_postgres_session')
    @patch('database.sqlite_db.get_sqlite_session')
    def test_fetch_and_store_shareholders_database_error(self, mock_sqlite_session, mock_postgres_session):
        """Test handling of database errors"""
        # Mock sessions to raise exceptions
        mock_sqlite_session.side_effect = Exception("SQLite error")
        mock_postgres_session.return_value = MagicMock()

        result = fetch_and_store_shareholders('TEST')

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0  # Empty DataFrame on error