
"""
Intraday Data module for Tehran Stock Exchange (Scraping Only)
Handles real-time and intraday trading data, order book, and trade history using web scraping.
"""

import requests
import pandas as pd
import jdatetime

def get_intraday_trades_scraping(symbol, date_str=None):
    """
    دریافت معاملات لحظه‌ای یک نماد با اسکرپینگ
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    # فرض بر این است که web-id نماد را دارید
    # اگر ندارید باید از lookup یا MarketWatch استخراج شود
    web_id = symbol if symbol.isdigit() else None
    if not web_id:
        # باید تابعی برای تبدیل نماد به web-id بنویسید یا از دیتافریم lookup استفاده کنید
        return None
    # تاریخ به فرمت مورد نیاز تبدیل شود
    if date_str is None:
        date_str = jdatetime.date.today().strftime('%Y%m%d')
    else:
        # فرض بر این است که ورودی شمسی است
        date_str = date_str.replace('-', '')
    url = f'http://old.tsetmc.com/tsev2/data/TradeDetail.aspx?i={web_id}&d={date_str}'
    try:
        r = requests.get(url, headers=headers)
    except Exception:
        return None
    trades = r.text.split(';')
    if not trades or trades == ['']:
        return pd.DataFrame()
    data = []
    for trade in trades:
        parts = trade.split(',')
        if len(parts) >= 6:
            data.append({
                'time': parts[0],
                'price': parts[1],
                'volume': parts[2],
                'value': parts[3],
                'buyer_id': parts[4],
                'seller_id': parts[5]
            })
    if not data:
        return pd.DataFrame()
    df = pd.DataFrame(data)
    # Ensure numeric columns are correct type for tests
    for col in ['price', 'volume', 'value']:
        if col in df:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def get_order_book_scraping(symbol):
    """
    دریافت اطلاعات سفارشات (Order Book) یک نماد با اسکرپینگ
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    web_id = symbol if symbol.isdigit() else None
    if not web_id:
        return None
    url = f'http://old.tsetmc.com/tsev2/data/InstOrderBook.aspx?i={web_id}'
    try:
        r = requests.get(url, headers=headers)
    except Exception:
        return None
    # داده‌ها باید پردازش شوند (فرمت خروجی را بررسی کنید)
    order_book = r.text.split(';')
    if not order_book or order_book == ['']:
        return None
    # نمونه ساده: فقط نمایش داده خام
    return order_book

def get_real_time_price_scraping(symbol):
    """
    دریافت قیمت لحظه‌ای یک نماد با اسکرپینگ
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    web_id = symbol if symbol.isdigit() else None
    if not web_id:
        return None
    url = f'http://old.tsetmc.com/tsev2/data/instinfodata.aspx?i={web_id}'
    try:
        r = requests.get(url, headers=headers)
    except Exception:
        return None
    price_data = r.text.split(',')
    if not price_data or price_data == ['']:
        return None
    # نمونه ساده: فقط نمایش داده خام
    return price_data

def get_trade_summary_scraping(symbol, date_str=None):
    """
    دریافت خلاصه معاملات لحظه‌ای یک نماد با اسکرپینگ
    """
    df = get_intraday_trades_scraping(symbol, date_str)
    if df is None:
        return None
    elif df.empty:
        return {
            'total_trades': 0,
            'total_volume': 0,
            'total_value': 0,
            'avg_price': 0,
            'max_price': 0,
            'min_price': 0
        }
    summary = {
        'total_trades': len(df),
        'total_volume': df['volume'].astype(float).sum(),
        'total_value': df['value'].astype(float).sum(),
        'avg_price': df['price'].astype(float).mean(),
        'max_price': df['price'].astype(float).max(),
        'min_price': df['price'].astype(float).min()
    }
    return summary
