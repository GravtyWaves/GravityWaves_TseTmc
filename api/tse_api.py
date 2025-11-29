import requests
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import time
from urllib.parse import urljoin

from config import API_BASE_URL, API_TIMEOUT, MAX_RETRIES, RETRY_DELAY

logger = logging.getLogger(__name__)

class TSEAPIClient:
    def __init__(self):
        self.base_url = "http://www.tsetmc.com/tsev2/data"

    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Any]:
        """ارسال درخواست به API با مدیریت خطا و retry"""
        url = urljoin(self.base_url, endpoint)

        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(url, params=params, timeout=API_TIMEOUT)
                response.raise_for_status()

                # بررسی محتوای پاسخ
                if response.headers.get('content-type', '').startswith('application/json'):
                    return response.json()
                else:
                    # برای پاسخ‌های غیر JSON، متن را برمی‌گردانیم
                    return response.text

            except requests.exceptions.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error(f"Request failed after {MAX_RETRIES} attempts: {e}")
                    return None
    
    def get_stock_list(self) -> Optional[List[Dict[str, Any]]]:
        """دریافت لیست تمام سهام"""
        logger.info("Fetching stock list from TSE API")
        return self._make_request("api/Stock/GetStockList")
    
    def get_stock_details(self, web_id: str) -> Optional[Dict[str, Any]]:
        """دریافت جزئیات یک سهم"""
        logger.info(f"Fetching stock details for web_id: {web_id}")
        return self._make_request(f"api/Stock/GetStockDetails/{web_id}")
    
    def get_current_date(self) -> str:
        """دریافت تاریخ جاری به فرمت شمسی"""
        today = datetime.now()
        # تبدیل به تاریخ شمسی (تقریبی)
        j_year = today.year - 621
        if today.month > 3 or (today.month == 3 and today.day >= 21):
            j_year += 1
        return f"{j_year:04d}/{today.month:02d}/{today.day:02d}"
    
    def get_date_range(self, days: int = 30) -> tuple[str, str]:
        """دریافت بازه زمانی برای روزهای گذشته"""
        today = datetime.now()
        past_date = today - timedelta(days=days)

        # تبدیل به تاریخ شمسی (تقریبی)
        def gregorian_to_jalali(g_date):
            g_year, g_month, g_day = g_date.year, g_date.month, g_date.day
            j_year = g_year - 621
            if g_month > 3 or (g_month == 3 and g_day >= 21):
                j_year += 1
            return f"{j_year:04d}/{g_month:02d}/{g_day:02d}"

        from_date = gregorian_to_jalali(past_date)
        to_date = gregorian_to_jalali(today)

        return from_date, to_date

    def get_instrument_search(self, query: str) -> Optional[str]:
        """جستجوی ابزار مالی"""
        logger.info(f"Searching for instrument: {query}")
        params = {'search': query}
        return self._make_request("InstrumentSearch", params)

    def get_instrument_info(self, web_id: str) -> Optional[str]:
        """دریافت اطلاعات ابزار مالی"""
        logger.info(f"Fetching instrument info for web_id: {web_id}")
        params = {'webId': web_id}
        return self._make_request("InstrumentInfo", params)

    def get_price_history(self, web_id: str, from_date: str, to_date: str) -> Optional[str]:
        """دریافت تاریخچه قیمت"""
        logger.info(f"Fetching price history for {web_id} from {from_date} to {to_date}")
        params = {
            'webId': web_id,
            'fromDate': from_date,
            'toDate': to_date
        }
        return self._make_request("PriceHistory", params)

    def get_client_type_history(self, web_id: str, from_date: str, to_date: str) -> Optional[str]:
        """دریافت تاریخچه حقیقی-حقوقی"""
        logger.info(f"Fetching client type history for {web_id} from {from_date} to {to_date}")
        params = {
            'webId': web_id,
            'fromDate': from_date,
            'toDate': to_date
        }
        return self._make_request("ClientTypeHistory", params)

    def get_index_history(self, index_id: str, from_date: str, to_date: str) -> Optional[str]:
        """دریافت تاریخچه شاخص"""
        logger.info(f"Fetching index history for {index_id} from {from_date} to {to_date}")
        params = {
            'indexId': index_id,
            'fromDate': from_date,
            'toDate': to_date
        }
        return self._make_request("IndexHistory", params)

    def get_shareholder_history(self, web_id: str, date: str) -> Optional[str]:
        """دریافت تاریخچه سهامداری"""
        logger.info(f"Fetching shareholder history for {web_id} on {date}")
        params = {
            'webId': web_id,
            'date': date
        }
        return self._make_request("ShareholderHistory", params)

    def get_intraday_trades(self, web_id: str, date: str) -> Optional[str]:
        """دریافت معاملات داخل روزی"""
        logger.info(f"Fetching intraday trades for {web_id} on {date}")
        params = {
            'webId': web_id,
            'date': date
        }
        return self._make_request("IntradayTrades", params)

    def get_usd_history(self, from_date: str, to_date: str) -> Optional[str]:
        """دریافت تاریخچه قیمت دلار"""
        logger.info(f"Fetching USD history from {from_date} to {to_date}")
        params = {
            'fromDate': from_date,
            'toDate': to_date
        }
        return self._make_request("USDHistory", params)

    def get_sector_index_history(self, sector_code: str, from_date: str, to_date: str) -> Optional[str]:
        """دریافت تاریخچه شاخص صنعت"""
        logger.info(f"Fetching sector index history for {sector_code} from {from_date} to {to_date}")
        params = {
            'sectorCode': sector_code,
            'fromDate': from_date,
            'toDate': to_date
        }
        return self._make_request("SectorIndexHistory", params)

    def parse_instrument_search(self, data: str) -> List[Dict[str, Any]]:
        """پارس کردن نتایج جستجوی ابزار مالی"""
        if not data or not data.strip():
            return []

        results = []
        for line in data.strip().split('\n'):
            if ',' not in line:
                continue
            parts = line.split(',')
            if len(parts) >= 3:
                results.append({
                    'ticker': parts[0].strip(),
                    'web_id': parts[1].strip(),
                    'name': parts[2].strip()
                })
        return results

    def parse_instrument_info(self, data: str) -> Optional[Dict[str, Any]]:
        """پارس کردن اطلاعات ابزار مالی"""
        if not data or ';' not in data:
            return None

        parts = data.split(';')
        if len(parts) >= 5:
            return {
                'web_id': parts[0].strip(),
                'name': parts[1].strip(),
                'market': parts[2].strip(),
                'ticker': parts[3].strip(),
                'tse_id': parts[4].strip()
            }
        return None

    def parse_price_history(self, data: str, stock_id: str) -> List[Dict[str, Any]]:
        """پارس کردن تاریخچه قیمت"""
        if not data or not data.strip():
            return []

        results = []
        for line in data.strip().split('\n'):
            if ',' not in line:
                continue
            parts = line.split(',')
            if len(parts) >= 8:
                try:
                    results.append({
                        'stock_id': stock_id,
                        'j_date': parts[0].strip(),
                        'open_price': int(parts[1]) if parts[1] else None,
                        'high_price': int(parts[2]) if parts[2] else None,
                        'low_price': int(parts[3]) if parts[3] else None,
                        'close_price': int(parts[4]) if parts[4] else None,
                        'volume': int(parts[5]) if parts[5] else None,
                        'value': int(parts[6]) if parts[6] else None,
                        'num_trades': int(parts[7]) if parts[7] else None
                    })
                except ValueError:
                    continue
        return results

    def parse_client_type_history(self, data: str, stock_id: str) -> List[Dict[str, Any]]:
        """پارس کردن تاریخچه حقیقی-حقوقی"""
        if not data or not data.strip():
            return []

        results = []
        for line in data.strip().split('\n'):
            if ',' not in line:
                continue
            parts = line.split(',')
            if len(parts) >= 9:
                try:
                    results.append({
                        'stock_id': stock_id,
                        'j_date': parts[0].strip(),
                        'vol_buy_r': int(parts[1]) if parts[1] else None,
                        'vol_sell_r': int(parts[2]) if parts[2] else None,
                        'val_buy_r': int(parts[3]) if parts[3] else None,
                        'val_sell_r': int(parts[4]) if parts[4] else None,
                        'vol_buy_l': int(parts[5]) if parts[5] else None,
                        'vol_sell_l': int(parts[6]) if parts[6] else None,
                        'val_buy_l': int(parts[7]) if parts[7] else None,
                        'val_sell_l': int(parts[8]) if parts[8] else None
                    })
                except ValueError:
                    continue
        return results

    def parse_index_history(self, data: str, index_id: str) -> List[Dict[str, Any]]:
        """پارس کردن تاریخچه شاخص"""
        if not data or not data.strip():
            return []

        results = []
        for line in data.strip().split('\n'):
            if ',' not in line:
                continue
            parts = line.split(',')
            if len(parts) >= 4:
                try:
                    results.append({
                        'index_id': index_id,
                        'j_date': parts[0].strip(),
                        'value': float(parts[1]) if parts[1] else None,
                        'volume': int(parts[2]) if parts[2] else None,
                        'change_percent': float(parts[3]) if parts[3] else None
                    })
                except ValueError:
                    continue
        return results

    def parse_shareholder_history(self, data: str, stock_id: str, j_date: str) -> List[Dict[str, Any]]:
        """پارس کردن تاریخچه سهامداری"""
        if not data or not data.strip():
            return []

        results = []
        for line in data.strip().split('\n'):
            if ',' not in line:
                continue
            parts = line.split(',')
            if len(parts) >= 4:
                try:
                    results.append({
                        'stock_id': stock_id,
                        'shareholder_id': parts[0].strip(),
                        'shareholder_name': parts[1].strip(),
                        'shares_count': int(parts[2]) if parts[2] else None,
                        'percentage': float(parts[3]) if parts[3] else None,
                        'j_date': j_date
                    })
                except ValueError:
                    continue
        return results

    def parse_intraday_trades(self, data: str, stock_id: str, j_date: str) -> List[Dict[str, Any]]:
        """پارس کردن معاملات داخل روزی"""
        if not data or not data.strip():
            return []

        results = []
        for line in data.strip().split('\n'):
            if ',' not in line:
                continue
            parts = line.split(',')
            if len(parts) >= 4:
                try:
                    results.append({
                        'stock_id': stock_id,
                        'j_date': j_date,
                        'time': parts[0].strip(),
                        'price': int(parts[1]) if parts[1] else None,
                        'volume': int(parts[2]) if parts[2] else None,
                        'value': int(parts[3]) if parts[3] else None
                    })
                except ValueError:
                    continue
        return results

    def parse_usd_history(self, data: str) -> List[Dict[str, Any]]:
        """پارس کردن تاریخچه قیمت دلار"""
        if not data or not data.strip():
            return []

        results = []
        for line in data.strip().split('\n'):
            if ',' not in line:
                continue
            parts = line.split(',')
            if len(parts) >= 4:
                try:
                    results.append({
                        'j_date': parts[0].strip(),
                        'price': float(parts[1]) if parts[1] else None,
                        'volume': int(parts[2]) if parts[2] else None,
                        'change_percent': float(parts[3]) if parts[3] else None
                    })
                except ValueError:
                    continue
        return results

    def parse_sector_index_history(self, data: str, sector_id: str) -> List[Dict[str, Any]]:
        """پارس کردن تاریخچه شاخص صنعت"""
        if not data or not data.strip():
            return []

        results = []
        for line in data.strip().split('\n'):
            if ',' not in line:
                continue
            parts = line.split(',')
            if len(parts) >= 4:
                try:
                    results.append({
                        'sector_id': sector_id,
                        'j_date': parts[0].strip(),
                        'value': float(parts[1]) if parts[1] else None,
                        'volume': int(parts[2]) if parts[2] else None,
                        'change_percent': float(parts[3]) if parts[3] else None
                    })
                except ValueError:
                    continue
        return results
