"""
Tests for api/parsers.py
"""

import pytest
import pandas as pd
from api.parsers import (
    parse_market_watch_scraped,
    parse_client_type_scraped,
    parse_order_book_scraped,
    parse_price_history_scraped
)


class TestParseMarketWatchScraped:
    """Tests for parse_market_watch_scraped"""

    def test_parse_market_watch_scraped_basic(self):
        """Test basic parsing of market watch data"""
        # Create sample data with 23 columns as expected
        sample_data = "1,1001,TICK1,Name1,10:00,1000,1010,1005,100,10000,10000000,995,1015,1000,10,1000,0,0,Sector1,1020,980,1000000,1"
        main_text = f"header1@header2@{sample_data}@footer"

        result = parse_market_watch_scraped(main_text)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 1
        assert list(result.columns) == ['WEB-ID','Ticker-Code','Ticker','Name','Time','Open','Final','Close','No','Volume','Value',
                                        'Low','High','Y-Final','EPS','Base-Vol','Unknown1','Unknown2','Sector','Day_UL','Day_LL','Share-No','Mkt-ID']
        assert result.iloc[0]['WEB-ID'] == '1'
        assert result.iloc[0]['Ticker'] == 'TICK1'

    def test_parse_market_watch_scraped_multiple_rows(self):
        """Test parsing multiple rows"""
        sample_data1 = "1,1001,TICK1,Name1,10:00,1000,1010,1005,100,10000,10000000,995,1015,1000,10,1000,0,0,Sector1,1020,980,1000000,1"
        sample_data2 = "2,1002,TICK2,Name2,10:01,1010,1020,1015,200,20000,20000000,1005,1025,1010,20,2000,0,0,Sector2,1030,990,2000000,2"
        main_text = f"header1@header2@{sample_data1};{sample_data2}@footer"

        result = parse_market_watch_scraped(main_text)

        assert len(result) == 2
        assert result.iloc[1]['WEB-ID'] == '2'

    def test_parse_market_watch_scraped_empty_data(self):
        """Test parsing with empty data"""
        main_text = "header1@header2@@footer"

        result = parse_market_watch_scraped(main_text)

        assert len(result) == 0
        assert list(result.columns) == ['WEB-ID','Ticker-Code','Ticker','Name','Time','Open','Final','Close','No','Volume','Value',
                                        'Low','High','Y-Final','EPS','Base-Vol','Unknown1','Unknown2','Sector','Day_UL','Day_LL','Share-No','Mkt-ID']


class TestParseClientTypeScraped:
    """Tests for parse_client_type_scraped"""

    def test_parse_client_type_scraped_basic(self):
        """Test basic parsing of client type data"""
        sample_data = "1,100,50,10000,5000,80,40,8000,4000"
        text = f"{sample_data};2,200,100,20000,10000,160,80,16000,8000"

        result = parse_client_type_scraped(text)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert list(result.columns) == ['WEB-ID','No_Buy_R','No_Buy_I','Vol_Buy_R','Vol_Buy_I','No_Sell_R','No_Sell_I','Vol_Sell_R','Vol_Sell_I']
        assert result.iloc[0]['WEB-ID'] == '1'
        assert result.iloc[0]['No_Buy_R'] == '100'

    def test_parse_client_type_scraped_single_row(self):
        """Test parsing single row"""
        sample_data = "1,100,50,10000,5000,80,40,8000,4000"
        text = sample_data

        result = parse_client_type_scraped(text)

        assert len(result) == 1
        assert result.iloc[0]['Vol_Buy_R'] == '10000'


class TestParseOrderBookScraped:
    """Tests for parse_order_book_scraped"""

    def test_parse_order_book_scraped_basic(self):
        """Test basic parsing of order book data"""
        sample_data = "1,5,10,8,1010,1005,1000,1200"
        text = f"{sample_data};2,3,15,12,1020,1015,1500,1800"

        result = parse_order_book_scraped(text)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert list(result.columns) == ['WEB-ID','OB-Depth','Sell-No','Buy-No','Buy-Price','Sell-Price','Buy-Vol','Sell-Vol']
        assert result.iloc[0]['WEB-ID'] == '1'
        assert result.iloc[0]['OB-Depth'] == '5'

    def test_parse_order_book_scraped_single_row(self):
        """Test parsing single row"""
        sample_data = "1,5,10,8,1010,1005,1000,1200"
        text = sample_data

        result = parse_order_book_scraped(text)

        assert len(result) == 1
        assert result.iloc[0]['Buy-Price'] == '1010'


class TestParsePriceHistoryScraped:
    """Tests for parse_price_history_scraped"""

    def test_parse_price_history_scraped_basic(self):
        """Test basic parsing of price history data"""
        sample_data = "1,1010,1005,100,10000,10000000,995,1015,1000,1000"
        text = f"{sample_data};2,1020,1015,200,20000,20000000,1005,1025,1010,1010"

        result = parse_price_history_scraped(text)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 2
        assert list(result.columns) == ['n','Final','Close','No','Volume','Value','Low','High','Y-Final','Open']
        assert result.iloc[0]['n'] == '1'
        assert result.iloc[0]['Final'] == '1010'

    def test_parse_price_history_scraped_single_row(self):
        """Test parsing single row"""
        sample_data = "1,1010,1005,100,10000,10000000,995,1015,1000,1000"
        text = sample_data

        result = parse_price_history_scraped(text)

        assert len(result) == 1
        assert result.iloc[0]['Volume'] == '10000'