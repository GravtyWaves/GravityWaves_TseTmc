
"""
Data Parser module for Tehran Stock Exchange (Scraping Only)
Handles parsing of various TSE data formats from web scraping.
"""

from typing import List, Dict, Any, Optional
import pandas as pd

def parse_market_watch_scraped(main_text: str) -> pd.DataFrame:
    """
    پارس داده‌های MarketWatch اسکرپ شده
    """
    Mkt_df = pd.DataFrame((main_text.split('@')[2]).split(';'))
    if Mkt_df.empty or Mkt_df.iloc[0, 0] == '':
        # Return empty DataFrame with correct columns
        return pd.DataFrame(columns=['WEB-ID','Ticker-Code','Ticker','Name','Time','Open','Final','Close','No','Volume','Value',
                                     'Low','High','Y-Final','EPS','Base-Vol','Unknown1','Unknown2','Sector','Day_UL','Day_LL','Share-No','Mkt-ID'])
    Mkt_df = Mkt_df[0].str.split(",", expand=True)
    # ستون‌ها را طبق Gravity_tse.py تنظیم کنید
    Mkt_df = Mkt_df.iloc[:,:23]
    Mkt_df.columns = ['WEB-ID','Ticker-Code','Ticker','Name','Time','Open','Final','Close','No','Volume','Value',
                      'Low','High','Y-Final','EPS','Base-Vol','Unknown1','Unknown2','Sector','Day_UL','Day_LL','Share-No','Mkt-ID']
    return Mkt_df

def parse_client_type_scraped(text: str) -> pd.DataFrame:
    """
    پارس داده‌های ClientTypeAll اسکرپ شده
    """
    if not text.strip():
        return pd.DataFrame(columns=['WEB-ID','No_Buy_R','No_Buy_I','Vol_Buy_R','Vol_Buy_I','No_Sell_R','No_Sell_I','Vol_Sell_R','Vol_Sell_I'])
    
    df = pd.DataFrame(text.split(';'))
    df = df[0].str.split(',', expand=True)
    df.columns = ['WEB-ID','No_Buy_R','No_Buy_I','Vol_Buy_R','Vol_Buy_I','No_Sell_R','No_Sell_I','Vol_Sell_R','Vol_Sell_I']
    return df

def parse_order_book_scraped(text: str) -> pd.DataFrame:
    """
    پارس داده‌های OrderBook اسکرپ شده
    """
    if not text.strip():
        return pd.DataFrame(columns=['WEB-ID','OB-Depth','Sell-No','Buy-No','Buy-Price','Sell-Price','Buy-Vol','Sell-Vol'])
    
    df = pd.DataFrame(text.split(';'))
    df = df[0].str.split(',', expand=True)
    df.columns = ['WEB-ID','OB-Depth','Sell-No','Buy-No','Buy-Price','Sell-Price','Buy-Vol','Sell-Vol']
    return df

def parse_price_history_scraped(text: str) -> pd.DataFrame:
    """
    پارس داده‌های ClosingPriceAll اسکرپ شده
    """
    if not text.strip():
        return pd.DataFrame(columns=['n','Final','Close','No','Volume','Value','Low','High','Y-Final','Open'])
    
    df = pd.DataFrame(text.split(';'))
    df.columns = ['Data']
    temp_data_df = df['Data'].str.split(',', expand=True)
    cols = ['n','Final','Close','No','Volume','Value','Low','High','Y-Final','Open']
    temp_data_df.columns = cols
    return temp_data_df
