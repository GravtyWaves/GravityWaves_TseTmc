"""
Tests for api/ri_history.py
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from api.ri_history import get_ri_history_scraping


class TestGetRIHistoryScraping:
    """Tests for get_ri_history_scraping"""

    @patch('api.ri_history.requests.get')
    def test_get_ri_history_scraping_success(self, mock_get):
        """Test successful scraping of RI history data"""
        # Mock the response
        mock_response = MagicMock()
        mock_response.text = "1,100,50,10000,5000,80,40,8000,4000;2,200,100,20000,10000,160,80,16000,8000"
        mock_get.return_value = mock_response

        result = get_ri_history_scraping()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert list(result.columns) == ['WEB-ID','No_Buy_R','No_Buy_I','Vol_Buy_R','Vol_Buy_I','No_Sell_R','No_Sell_I','Vol_Sell_R','Vol_Sell_I']
        assert result.iloc[0]['WEB-ID'] == '1'
        assert result.iloc[0]['No_Buy_R'] == '100'

        # Verify the request was made correctly
        mock_get.assert_called_once_with('http://old.tsetmc.com/tsev2/data/ClientTypeAll.aspx',
                                        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})

    @patch('api.ri_history.requests.get')
    def test_get_ri_history_scraping_single_row(self, mock_get):
        """Test scraping with single row of data"""
        mock_response = MagicMock()
        mock_response.text = "1,100,50,10000,5000,80,40,8000,4000"
        mock_get.return_value = mock_response

        result = get_ri_history_scraping()

        assert len(result) == 1
        assert result.iloc[0]['Vol_Buy_I'] == '5000'

    @patch('api.ri_history.requests.get')
    def test_get_ri_history_scraping_empty_response(self, mock_get):
        """Test scraping with empty response"""
        mock_response = MagicMock()
        mock_response.text = ""
        mock_get.return_value = mock_response

        result = get_ri_history_scraping()

        assert len(result) == 0  # Empty DataFrame
        assert list(result.columns) == ['WEB-ID','No_Buy_R','No_Buy_I','Vol_Buy_R','Vol_Buy_I','No_Sell_R','No_Sell_I','Vol_Sell_R','Vol_Sell_I']

    @patch('api.ri_history.requests.get')
    def test_get_ri_history_scraping_request_exception(self, mock_get):
        """Test handling of request exceptions"""
        mock_get.side_effect = Exception("Network error")

        with pytest.raises(Exception, match="Network error"):
            get_ri_history_scraping()