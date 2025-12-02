"""
Tests for api/scraper.py
"""

import pytest
import pandas as pd
import os
import tempfile
from unittest.mock import patch, MagicMock
from api.scraper import (
    build_market_stock_list,
    get_market_watch,
    get_60d_price_history,
    get_shareholders_info
)


class TestBuildMarketStockList:
    """Tests for build_market_stock_list"""

    @patch('api.scraper.jdatetime.datetime')
    @patch('api.scraper.pd.DataFrame.to_excel')
    @patch('api.scraper.pd.DataFrame.to_csv')
    def test_build_market_stock_list_basic(self, mock_to_csv, mock_to_excel, mock_jdatetime):
        """Test basic functionality of build_market_stock_list"""
        mock_jdatetime.now.return_value.strftime.return_value = "2023-10-01"

        result = build_market_stock_list()

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ['Ticker', 'Name', 'Market', 'WEB-ID']
        assert len(result) == 0

        # Verify file saving calls
        mock_to_excel.assert_called_once_with('D:/FinPy-TSE Data/2023-10-01_StockList.xlsx')
        mock_to_csv.assert_called_once_with('D:/FinPy-TSE Data/2023-10-01_StockList.csv')

    @patch('api.scraper.jdatetime.datetime')
    @patch('api.scraper.pd.DataFrame.to_excel')
    @patch('api.scraper.pd.DataFrame.to_csv')
    def test_build_market_stock_list_no_save(self, mock_to_csv, mock_to_excel, mock_jdatetime):
        """Test with save options disabled"""
        result = build_market_stock_list(save_excel=False, save_csv=False)

        mock_to_excel.assert_not_called()
        mock_to_csv.assert_not_called()

    @patch('api.scraper.jdatetime.datetime')
    @patch('api.scraper.pd.DataFrame.to_excel')
    @patch('api.scraper.pd.DataFrame.to_csv')
    def test_build_market_stock_list_save_path_formatting(self, mock_to_csv, mock_to_excel, mock_jdatetime):
        """Test save path formatting"""
        mock_jdatetime.now.return_value.strftime.return_value = "2023-10-01"

        result = build_market_stock_list(save_path='D:/FinPy-TSE Data')

        mock_to_excel.assert_called_once_with('D:/FinPy-TSE Data/2023-10-01_StockList.xlsx')
        mock_to_csv.assert_called_once_with('D:/FinPy-TSE Data/2023-10-01_StockList.csv')

    @patch('api.scraper.jdatetime.datetime')
    @patch('api.scraper.pd.DataFrame.to_excel')
    @patch('api.scraper.pd.DataFrame.to_csv')
    def test_build_market_stock_list_save_path_with_slash(self, mock_to_csv, mock_to_excel, mock_jdatetime):
        """Test save path with trailing slash"""
        mock_jdatetime.now.return_value.strftime.return_value = "2023-10-01"

        result = build_market_stock_list(save_path='D:/FinPy-TSE Data/')

        mock_to_excel.assert_called_once_with('D:/FinPy-TSE Data/2023-10-01_StockList.xlsx')


class TestGetMarketWatch:
    """Tests for get_market_watch"""

    @patch('api.scraper.requests.get')
    @patch('api.scraper.jdatetime.datetime')
    @patch('api.scraper.pd.DataFrame.to_excel')
    def test_get_market_watch_success(self, mock_to_excel, mock_jdatetime, mock_get):
        """Test successful market watch data retrieval"""
        mock_response = MagicMock()
        mock_response.text = "header1@header2@1,1001,SYMBOL1,Name1,Sector1,1000,1010,990,1005,1005,100,10000,1000000,1000,10,1000,0,0,1015,985,1000000,1,extra"
        mock_get.return_value = mock_response
        mock_jdatetime.now.return_value.strftime.return_value = "2023-10-01"

        result = get_market_watch()

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        expected_cols = ['WEB-ID','Ticker-Code','symbol','Name','Sector','Open','High','Low','Final','last_price','No','Volume','Value',
                        'Y-Final','EPS','Base-Vol','Unknown1','Unknown2','Day_UL','Day_LL','Share-No','Mkt-ID','Extra']
        assert list(result.columns) == expected_cols

        # Check numeric conversion
        assert result.iloc[0]['Volume'] == 10000
        assert result.iloc[0]['Final'] == 1005

        mock_get.assert_called_once_with('http://old.tsetmc.com/tsev2/data/MarketWatchPlus.aspx',
                                        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})

    @patch('api.scraper.requests.get')
    def test_get_market_watch_empty_data(self, mock_get):
        """Test with empty market watch data"""
        mock_response = MagicMock()
        mock_response.text = "header1@header2@"
        mock_get.return_value = mock_response

        result = get_market_watch(save_excel=False)

        assert len(result) == 0

    @patch('api.scraper.requests.get')
    def test_get_market_watch_request_exception(self, mock_get):
        """Test handling of request exceptions"""
        mock_get.side_effect = Exception("Network error")

        with pytest.raises(Exception, match="Network error"):
            get_market_watch(save_excel=False)


class TestGet60DPriceHistory:
    """Tests for get_60d_price_history"""

    @patch('api.scraper.requests.get')
    @patch('api.scraper.jdatetime.datetime')
    @patch('api.scraper.pd.DataFrame.to_excel')
    def test_get_60d_price_history_success(self, mock_to_excel, mock_jdatetime, mock_get):
        """Test successful 60d price history retrieval"""
        mock_response = MagicMock()
        mock_response.text = "data1;data2;data3"
        mock_get.return_value = mock_response
        mock_jdatetime.now.return_value.strftime.return_value = "2023-10-01"

        stock_list = ['stock1', 'stock2']
        result = get_60d_price_history(stock_list)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert list(result.columns) == ['Data']
        assert result.iloc[0]['Data'] == 'data1'

        mock_get.assert_called_once_with('http://old.tsetmc.com/tsev2/data/ClosingPriceAll.aspx',
                                        headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})

    @patch('api.scraper.requests.get')
    def test_get_60d_price_history_no_save(self, mock_get):
        """Test without saving"""
        mock_response = MagicMock()
        mock_response.text = "data1"
        mock_get.return_value = mock_response

        stock_list = ['stock1']
        result = get_60d_price_history(stock_list, save_excel=False)

        assert len(result) == 1


class TestGetShareholdersInfo:
    """Tests for get_shareholders_info"""

    def test_get_shareholders_info_basic(self):
        """Test basic shareholder info retrieval"""
        result = get_shareholders_info()

        assert isinstance(result, pd.DataFrame)
        assert list(result.columns) == ['Name', 'ShareNo', 'SharePct', 'Changes', 'Ticker', 'Market']
        assert len(result) == 0

    def test_get_shareholders_info_with_ticker(self):
        """Test with ticker parameter"""
        result = get_shareholders_info(ticker='TEST')

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0  # Still empty as it's a stub