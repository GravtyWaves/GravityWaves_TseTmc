
"""
Web Scraper module for Tehran Stock Exchange
Based on Gravity_tse.py logic, only uses web scraping (no API dependency)
"""

import requests
import pandas as pd
import jdatetime
import calendar

def build_market_stock_list(bourse=True, farabourse=True, payeh=True, detailed_list=True, show_progress=True, save_excel=True, save_csv=True, save_path='D:/FinPy-TSE Data/'):
    """
    Collects stock list from TSE website using web scraping.
    Returns a DataFrame and optionally saves to Excel/CSV.
    """
    # This function is a simplified version of Build_Market_StockList from Gravity_tse.py
    # For demonstration, just create an empty DataFrame
    look_up = pd.DataFrame({'Ticker':[], 'Name':[], 'Market':[], 'WEB-ID':[]})
    if save_excel:
        if save_path[-1] != '/':
            save_path = save_path + '/'
        today_j_date = jdatetime.datetime.now().strftime("%Y-%m-%d")
        try:
            look_up.to_excel(save_path + today_j_date + '_StockList.xlsx')
        except Exception as e:
            print('Error saving Excel:', e)
    if save_csv:
        if save_path[-1] != '/':
            save_path = save_path + '/'
        today_j_date = jdatetime.datetime.now().strftime("%Y-%m-%d")
        try:
            look_up.to_csv(save_path + today_j_date + '_StockList.csv')
        except Exception as e:
            print('Error saving CSV:', e)
    return look_up

def get_market_watch(save_excel=True, save_path='D:/FinPy-TSE Data/MarketWatch'):
    """
    Collects market watch data from TSE website using web scraping.
    Returns a DataFrame and optionally saves to Excel.
    """
    # This function is a simplified version of Get_MarketWatch from Gravity_tse.py
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    r = requests.get('http://old.tsetmc.com/tsev2/data/MarketWatchPlus.aspx', headers=headers)
    main_text = r.text
    rows = (main_text.split('@')[2]).split(';')
    df = pd.DataFrame([row.split(',') for row in rows if row])
    expected_cols = ['WEB-ID','Ticker-Code','symbol','Name','Sector','Open','High','Low','Final','last_price','No','Volume','Value',
                    'Y-Final','EPS','Base-Vol','Unknown1','Unknown2','Day_UL','Day_LL','Share-No','Mkt-ID','Extra']
    df = df.iloc[:,:len(expected_cols)]
    df.columns = expected_cols[:df.shape[1]]
    # تبدیل مقادیر عددی
    for col in ['last_price','Open','High','Low','Final','Volume','Value']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    if save_excel:
        if save_path[-1] != '/':
            save_path = save_path + '/'
        today_j_date = jdatetime.datetime.now().strftime("%Y-%m-%d")
        try:
            df.to_excel(save_path + today_j_date + '_MarketWatch.xlsx')
        except Exception as e:
            print('Error saving Excel:', e)
    return df

def get_60d_price_history(stock_list, adjust_price=True, show_progress=True, save_excel=False, save_path='D:/FinPy-TSE Data/MarketWatch'):
    """
    Collects last 60 days price history for a list of stocks using web scraping.
    Returns a DataFrame and optionally saves to Excel.
    """
    # This function is a simplified version of Get_60D_PriceHistory from Gravity_tse.py
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    r = requests.get('http://old.tsetmc.com/tsev2/data/ClosingPriceAll.aspx', headers=headers)
    hist_60_days = pd.DataFrame(r.text.split(';'))
    hist_60_days.columns = ['Data']
    # Additional processing can be added here
    if save_excel:
        if save_path[-1] != '/':
            save_path = save_path + '/'
        today_j_date = jdatetime.datetime.now().strftime("%Y-%m-%d")
        try:
            hist_60_days.to_excel(save_path + today_j_date + '_60D_History.xlsx')
        except Exception as e:
            print('Error saving Excel:', e)
    return hist_60_days

def get_shareholders_info(ticker='خودرو'):
    """
    Collects shareholder information for a ticker using web scraping.
    Returns a DataFrame.
    """
    # This function is a simplified version of Get_ShareHoldersInfo from Gravity_tse.py
    # For demonstration, just create an empty DataFrame
    df_sh = pd.DataFrame({'Name':[], 'ShareNo':[], 'SharePct':[], 'Changes':[], 'Ticker':[], 'Market':[]})
    return df_sh
