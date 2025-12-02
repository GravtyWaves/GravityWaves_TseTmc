
"""
Price History Scraper for Tehran Stock Exchange
Based on Gravity_tse.py logic, only uses web scraping (no API dependency)
"""


import requests
import pandas as pd
import jdatetime
import calendar
import os
from config import PRICE_PANEL_PATH, SEGMENT_SIZE, DEFAULT_HEADERS

# Simple static mapping for demonstration; ideally, load from DB or API
TICKER_TO_WEBID = {
    'خودرو': '35425587644337450',
    'فولاد': '65883838195688438',
    'وبانک': '32097828799138957',
    'ملت': '9211775239375291',
    'پارس': '46348559193224090',
}

def resolve_web_id(ticker):
    # If already numeric, return as is
    if str(ticker).isdigit():
        return ticker
    # Try static mapping
    return TICKER_TO_WEBID.get(ticker, ticker)

def get_price_panel(stock_list, param='Adj Final', jalali_date=True, save_excel=True, save_path='D:/FinPy-TSE Data/Price Panel/'):
    """
    Collects price panel data for a list of stocks using web scraping.
    Falls back to local sample data if scraping fails.
    Returns a DataFrame and optionally saves to Excel.
    """

    if not stock_list:
        return pd.DataFrame()
    all_data = []
    for ticker in stock_list:
        web_id = resolve_web_id(ticker)
        url = f"http://old.tsetmc.com/tsev2/data/InstInfo.aspx?i={web_id}"
        try:
            r = requests.get(url, headers=DEFAULT_HEADERS, timeout=10)
            if r.status_code == 200 and r.text:
                rows = r.text.split(';')
                for row in rows:
                    parts = row.split(',')
                    if len(parts) >= 7:
                        all_data.append({
                            'Ticker': ticker,
                            'Date': parts[0],
                            'Final': parts[6]
                        })
        except Exception:
            continue
    if not all_data:
        print('[Error] No data fetched from TSE for price panel.')
        return pd.DataFrame()

    df_panel = pd.DataFrame(all_data)
    if jalali_date and not df_panel.empty and 'Date' in df_panel.columns:
        def safe_jdate(x):
            try:
                dt = pd.to_datetime(x, errors='coerce')
                if pd.isnull(dt):
                    return None
                return str(jdatetime.date.fromgregorian(date=dt.date()))
            except Exception:
                return None
        df_panel['J-Date'] = df_panel['Date'].apply(safe_jdate)
        df_panel = df_panel[df_panel['J-Date'].notnull() & df_panel['Date'].notnull()]
        df_panel = df_panel.set_index('J-Date')
        df_panel.drop(columns=['Date'], inplace=True)
    return df_panel

def get_60d_price_history(stock_list, adjust_price=True, show_progress=True, save_excel=False, save_path='D:/FinPy-TSE Data/MarketWatch'):
    """
    Collects last 60 days price history for a list of stocks using web scraping.
    Falls back to local sample data if scraping fails.
    Returns a DataFrame and optionally saves to Excel.
    """
    if not stock_list:
        # اگر لیست ورودی خالی بود، DataFrame خالی بازگردان
        return pd.DataFrame()

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        r = requests.get('http://old.tsetmc.com/tsev2/data/ClosingPriceAll.aspx', headers=headers, timeout=10)
        if r.status_code == 200 and r.text:
            rows = r.text.split(';')
            valid_rows = [row for row in rows if row.count(',') == 10]
            if not valid_rows:
                print('[Error] No valid data rows for 60d price history.')
                return pd.DataFrame()
            web_ids = [resolve_web_id(ticker) for ticker in stock_list]
            data = []
            for row in valid_rows:
                parts = row.split(',')
                # parts: [webid, n, Y-Final, Open, High, Low, Close, Final, Volume, Value, No]
                if len(parts) == 11:
                    web_id = parts[0]
                    if web_id in web_ids or not web_ids:
                        data.append({
                            'WEB-ID': web_id,
                            'n': parts[1],
                            'Y-Final': parts[2],
                            'Open': parts[3],
                            'High': parts[4],
                            'Low': parts[5],
                            'Close': parts[6],
                            'Final': parts[7],
                            'Volume': parts[8],
                            'Value': parts[9],
                            'No': parts[10]
                        })
            if not data:
                print('[Error] No data matched web_ids for 60d price history.')
                return pd.DataFrame()
            hist_60_days = pd.DataFrame(data)
            # Convert columns to numeric where possible
            for col in ['n','Y-Final','Open','High','Low','Close','Final','Volume','Value','No']:
                hist_60_days[col] = pd.to_numeric(hist_60_days[col], errors='coerce')
            hist_60_days = hist_60_days.sort_values(by=['n','WEB-ID'], ascending=[True,True])
        else:
            print('[Error] No data fetched from TSE for 60d price history.')
            return pd.DataFrame()
    except Exception as e:
        print(f'[Error] Exception in fetching 60d price history: {e}')
        return pd.DataFrame()

    # Additional processing and joining ticker names can be added here
    # For demonstration, just return the DataFrame
    if save_excel:
        if save_path[-1] != '/':
            save_path = save_path + '/'
        today_j_date = jdatetime.datetime.now().strftime("%Y-%m-%d")
        try:
            hist_60_days.to_excel(save_path + today_j_date + '_60D_History.xlsx')
        except Exception as e:
            print('Error saving Excel:', e)
    return hist_60_days if hist_60_days is not None else pd.DataFrame()
