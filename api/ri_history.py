
"""
Retail-Institutional History module for Tehran Stock Exchange (Scraping Only)
Handles retail vs institutional trading data and analysis using web scraping.
"""

import requests
import pandas as pd

def get_ri_history_scraping():
    """
    دریافت داده‌های خرید و فروش حقیقی و حقوقی با اسکرپینگ
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    r = requests.get('http://old.tsetmc.com/tsev2/data/ClientTypeAll.aspx', headers=headers)
    if not r.text.strip():
        return pd.DataFrame(columns=['WEB-ID','No_Buy_R','No_Buy_I','Vol_Buy_R','Vol_Buy_I','No_Sell_R','No_Sell_I','Vol_Sell_R','Vol_Sell_I'])
    
    df = pd.DataFrame(r.text.split(';'))
    df = df[0].str.split(',', expand=True)
    df.columns = ['WEB-ID','No_Buy_R','No_Buy_I','Vol_Buy_R','Vol_Buy_I','No_Sell_R','No_Sell_I','Vol_Sell_R','Vol_Sell_I']
    return df
