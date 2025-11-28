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
        self.base_url = API_BASE_URL
        self.session = requests.Session()
        self.session.timeout = API_TIMEOUT
        
    def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """ارسال درخواست به API با مدیریت خطا و retry"""
        url = urljoin(self.base_url, endpoint)
        
        for attempt in range(MAX_RETRIES):
            try:
                response = self.session.get(url, params=params)
                response.raise_for_status()
                
                # بررسی محتوای پاسخ
                if response.headers.get('content-type', '').startswith('application/json'):
                    return response.json()
                else:
                    logger.warning(f"Non-JSON response from {url}")
                    return None
                    
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
    
    def get_price_history(self, web_id: str, from_date: str, to_date: str) -> Optional[List[Dict[str, Any]]]:
        """دریافت تاریخچه قیمت یک سهم"""
        logger.info(f"Fetching price history for {web_id} from {from_date} to {to_date}")
        params = {
            'webId': web_id,
            'fromDate': from_date,
            'toDate': to_date
        }
        return self._make_request("api/Stock/GetPriceHistory", params)
    
    def get_ri_history(self, web_id: str, from_date: str, to_date: str) -> Optional[List[Dict[str, Any]]]:
        """دریافت تاریخچه حقیقی-حقوقی یک سهم"""
        logger.info(f"Fetching RI history for {web_id} from {from_date} to {to_date}")
        params = {
            'webId': web_id,
            'fromDate': from_date,
            'toDate': to_date
        }
        return self._make_request("api/Stock/GetRIHistory", params)
    
    def get_index_list(self) -> Optional[List[Dict[str, Any]]]:
        """دریافت لیست شاخص‌ها"""
        logger.info("Fetching index list from TSE API")
        return self._make_request("api/Index/GetIndexList")
    
    def get_index_history(self, web_id: str, from_date: str, to_date: str) -> Optional[List[Dict[str, Any]]]:
        """دریافت تاریخچه شاخص"""
        logger.info(f"Fetching index history for {web_id} from {from_date} to {to_date}")
        params = {
            'webId': web_id,
            'fromDate': from_date,
            'toDate': to_date
        }
        return self._make_request("api/Index/GetIndexHistory", params)
    
    def get_sector_list(self) -> Optional[List[Dict[str, Any]]]:
        """دریافت لیست صنایع"""
        logger.info("Fetching sector list from TSE API")
        return self._make_request("api/Sector/GetSectorList")
    
    def get_sector_index_history(self, sector_code: str, from_date: str, to_date: str) -> Optional[List[Dict[str, Any]]]:
        """دریافت تاریخچه شاخص صنعت"""
        logger.info(f"Fetching sector index history for {sector_code} from {from_date} to {to_date}")
        params = {
            'sectorCode': sector_code,
            'fromDate': from_date,
            'toDate': to_date
        }
        return self._make_request("api/Sector/GetSectorIndexHistory", params)
    
    def get_shareholder_history(self, web_id: str, from_date: str, to_date: str) -> Optional[List[Dict[str, Any]]]:
        """دریافت تاریخچه سهامداری عمده"""
        logger.info(f"Fetching shareholder history for {web_id} from {from_date} to {to_date}")
        params = {
            'webId': web_id,
            'fromDate': from_date,
            'toDate': to_date
        }
        return self._make_request("api/Stock/GetShareholderHistory", params)
    
    def get_intraday_trades(self, web_id: str, date: str) -> Optional[List[Dict[str, Any]]]:
        """دریافت معاملات داخل روزی"""
        logger.info(f"Fetching intraday trades for {web_id} on {date}")
        params = {
            'webId': web_id,
            'date': date
        }
        return self._make_request("api/Stock/GetIntradayTrades", params)
    
    def get_usd_history(self, from_date: str, to_date: str) -> Optional[List[Dict[str, Any]]]:
        """دریافت تاریخچه قیمت دلار"""
        logger.info(f"Fetching USD history from {from_date} to {to_date}")
        params = {
            'fromDate': from_date,
            'toDate': to_date
        }
        return self._make_request("api/USD/GetUSDHistory", params)
    
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
