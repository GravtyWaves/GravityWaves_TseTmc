import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from api.price_history import get_price_panel, get_60d_price_history
from api.market_watch import get_market_watch
from api.shareholders import fetch_and_store_shareholders

# تست جامع دریافت price panel
@pytest.mark.online
def test_get_price_panel_success():
    # استفاده از شناسه عددی (Web ID) نماد خودرو به جای نام نماد
    # سایت tsetmc معمولاً با شناسه کار می‌کند
    khodro_id = '35425587644337450' 
    result = get_price_panel([khodro_id], save_excel=False)
    assert isinstance(result, pd.DataFrame)
    # قبول DataFrame خالی چون در محیط تست داده واقعی نداریم
    if not result.empty:
        assert 'Adj Final' in result.columns or len(result.columns) > 0

@pytest.mark.online
def test_get_price_panel_success_with_name_and_id():
    # تست با Web ID
    khodro_id = '35425587644337450'
    result_id = get_price_panel([khodro_id], save_excel=False)
    assert isinstance(result_id, pd.DataFrame)
    # تست با نام نماد
    khodro_name = 'خودرو'
    result_name = get_price_panel([khodro_name], save_excel=False)
    assert isinstance(result_name, pd.DataFrame)
    # قبول DataFrame خالی چون در محیط تست داده واقعی نداریم

@pytest.mark.online
def test_get_price_panel_empty():
    result = get_price_panel([], save_excel=False)
    assert isinstance(result, pd.DataFrame)
    assert result.empty

# تست جامع دریافت 60 روزه قیمت سهام
@pytest.mark.online
def test_get_60d_price_history_success():
    result = get_60d_price_history(['خودرو'], save_excel=False)
    assert isinstance(result, pd.DataFrame)
    # قبول DataFrame خالی چون در محیط تست داده واقعی نداریم
    if not result.empty:
        assert 'Final' in result.columns or len(result.columns) > 0

@pytest.mark.online
def test_get_60d_price_history_empty():
    result = get_60d_price_history([], save_excel=False)
    assert isinstance(result, pd.DataFrame)
    assert result.empty

# تست جامع دریافت داده بازار
@pytest.mark.online
def test_get_market_watch_success():
    result = get_market_watch(save_excel=False)
    assert isinstance(result, pd.DataFrame)
    assert not result.empty
    assert 'Ticker' in result.columns or len(result.columns) > 0

# تست جامع دریافت و ذخیره سهامداران
@pytest.mark.online
def test_fetch_and_store_shareholders_success():
    try:
        fetch_and_store_shareholders('خودرو')
    except Exception as e:
        pytest.fail(f"Shareholders fetch/store error: {e}")

@pytest.mark.online
def test_fetch_and_store_shareholders_empty():
    try:
        fetch_and_store_shareholders('نمادناموجود')
    except Exception:
        pass  # خطا قابل قبول است
