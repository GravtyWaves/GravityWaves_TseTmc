
import pytest
import pandas as pd
from api.price_history import get_price_panel, get_60d_price_history
from api.market_watch import get_market_watch
from api.shareholders import fetch_and_store_shareholders

def test_get_price_panel():
    result = get_price_panel(['خودرو'], save_excel=False)
    assert isinstance(result, pd.DataFrame)

def test_get_60d_price_history():
    result = get_60d_price_history(['خودرو'], save_excel=False)
    assert isinstance(result, pd.DataFrame)

def test_get_market_watch():
    result = get_market_watch(save_excel=False)
    assert isinstance(result, pd.DataFrame)

def test_fetch_and_store_shareholders():
    # فقط بررسی اجرا بدون خطا
    try:
        fetch_and_store_shareholders('خودرو')
    except Exception as e:
        assert False, f"Error in fetch_and_store_shareholders: {e}"
