"""
کلاس TSE API Client - دریافت داده واقعی از بورس تهران
"""
import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from utils.helpers import parse_jalali_date

class TSEAPIClient:
    """API Client برای دریافت داده از سایت tsetmc.com"""
    
    def __init__(self, timeout=30):
        self.base_url = "http://old.tsetmc.com"
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def _make_request(self, url, params=None, timeout=None, max_retries=3):
        """متد کمکی برای ارسال درخواست HTTP با retry"""
        if timeout is None:
            timeout = self.timeout
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, params=params, timeout=timeout)
                response.raise_for_status()
                text = response.text
                
                # بررسی اینکه پاسخ HTML صفحه خطا نباشد
                if text and ('<!doctype html>' in text.lower() or '<html>' in text.lower()):
                    # اگر HTML برگشت و URL شامل .aspx است، احتمالاً خطا است
                    if '.aspx' in url and len(text) < 5000:
                        return None
                
                return text
            except Exception as e:
                print(f"Request error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(2 * (attempt + 1))  # Exponential backoff
                    continue
                return None
        return None
    
    def get_stock_list(self):
        """دریافت لیست سهام از TSE"""
        try:
            url = f"{self.base_url}/tsev2/data/MarketWatchPlus.aspx"
            data = self._make_request(url)
            if not data or len(data) < 10:
                return []
            
            # فرمت: header@header@data
            parts = data.split('@')
            if len(parts) < 3:
                return []
            
            stocks = []
            rows = parts[2].split(';')
            for row in rows:
                if not row:
                    continue
                cols = row.split(',')
                if len(cols) >= 8:
                    # تبدیل SectorCode به float
                    sector_code = None
                    if len(cols) > 17 and cols[17]:
                        try:
                            sector_code = float(cols[17])
                        except (ValueError, TypeError):
                            sector_code = None
                    
                    stocks.append({
                        'InsCode': cols[0],
                        'InstrumentID': cols[1],
                        'Symbol': cols[2],
                        'Name': cols[3],
                        'ticker': cols[2],
                        'name': cols[3],
                        'web_id': cols[0],
                        'SectorCode': sector_code
                    })
            return stocks
        except Exception as e:
            print(f"Error fetching stock list: {e}")
            return []
    
    def get_sector_list(self):
        """دریافت لیست صنایع"""
        # استخراج صنایع از لیست سهام
        stocks = self.get_stock_list()
        sectors = {}
        for stock in stocks:
            sector_code_str = stock.get('SectorCode', '')
            if sector_code_str:
                try:
                    # تبدیل به float برای سازگاری با database model
                    sector_code = float(sector_code_str)
                    if sector_code not in sectors:
                        sectors[sector_code] = {
                            'SectorCode': sector_code,
                            'SectorName': f'صنعت {int(sector_code)}',
                            'SectorNameEn': f'Sector {int(sector_code)}'
                        }
                except (ValueError, TypeError):
                    continue
        return list(sectors.values())
    
    def get_index_list(self):
        """دریافت لیست شاخص‌ها"""
        # شاخص‌های اصلی بورس
        return [
            {'IndexName': 'شاخص کل', 'IndexNameEn': 'TEDPIX', 'InsCode': '32097828799138957', 'name': 'شاخص کل', 'web_id': '32097828799138957'},
            {'IndexName': 'شاخص کل هم وزن', 'IndexNameEn': 'TEDIX', 'InsCode': '67130298613737888', 'name': 'شاخص کل هم وزن', 'web_id': '67130298613737888'},
            {'IndexName': 'شاخص قیمت', 'IndexNameEn': 'TEDFIX', 'InsCode': '62752761908615603', 'name': 'شاخص قیمت', 'web_id': '62752761908615603'}
        ]
    
    def get_date_range(self, days=30):
        """دریافت بازه زمانی"""
        today = datetime.now()
        past_date = today - timedelta(days=days)
        
        # تبدیل تقریبی به تاریخ شمسی
        def to_jalali(d):
            j_year = d.year - 621
            if d.month > 3 or (d.month == 3 and d.day >= 21):
                j_year += 1
            return f"{j_year:04d}/{d.month:02d}/{d.day:02d}"
        
        return (to_jalali(past_date), to_jalali(today))
    
    def get_price_history(self, web_id, from_date, to_date):
        """دریافت تاریخچه قیمت"""
        try:
            url = f"{self.base_url}/tsev2/data/ClientTypeHistory.aspx"
            params = {'i': web_id}
            return self._make_request(url, params=params)
        except:
            return None
    
    def parse_price_history(self, raw, stock_id):
        """پارس تاریخچه قیمت"""
        if not raw:
            return []
        
        results = []
        for line in raw.strip().split('\n'):
            if ',' not in line:
                continue
            parts = line.split(',')
            if len(parts) >= 8:
                try:
                    results.append({
                        'stock_id': stock_id,
                        'j_date': parts[0],
                        'date': parse_jalali_date(parts[0]),
                        'open_price': int(parts[1]) if parts[1] else None,
                        'high_price': int(parts[2]) if parts[2] else None,
                        'low_price': int(parts[3]) if parts[3] else None,
                        'close_price': int(parts[4]) if parts[4] else None,
                        'volume': int(parts[5]) if parts[5] else None,
                        'value': int(parts[6]) if parts[6] else None,
                        'num_trades': int(parts[7]) if parts[7] else None
                    })
                except:
                    continue
        return results
    
    def get_client_type_history(self, web_id, from_date, to_date):
        """دریافت تاریخچه حقیقی-حقوقی"""
        return self.get_price_history(web_id, from_date, to_date)
    
    def parse_client_type_history(self, raw, stock_id):
        """پارس تاریخچه حقیقی-حقوقی"""
        return self.parse_price_history(raw, stock_id)
    
    def get_stock_details(self, web_id):
        """دریافت جزئیات سهم"""
        return None
    
    def get_instrument_info(self, web_id):
        """دریافت اطلاعات ابزار"""
        try:
            url = f"{self.base_url}/Loader.aspx?ParTree=151311&i={web_id}"
            response = self._make_request(url, timeout=10)
            if response and len(response) > 100:
                return response
            return None
        except:
            return None
    
    def get_shareholder_history(self, web_id, date):
        """دریافت تاریخچه سهامداران"""
        try:
            url = f"{self.base_url}/tsev2/data/ShareHolder.aspx?i={web_id}"
            response = self._make_request(url, timeout=10)
            return response if response else None
        except:
            return None
    
    def get_intraday_trades(self, web_id, date=None):
        """دریافت معاملات روزانه"""
        try:
            url = f"{self.base_url}/tsev2/data/InstTradeHistory.aspx?i={web_id}"
            if date:
                url += f"&d={date}"
            response = self._make_request(url, timeout=10)
            return response if response else None
        except:
            return None
    
    def get_current_date(self):
        """دریافت تاریخ جاری"""
        today = datetime.now()
        j_year = today.year - 621
        if today.month > 3 or (today.month == 3 and today.day >= 21):
            j_year += 1
        return f"{j_year:04d}/{today.month:02d}/{today.day:02d}"
    
    def get_instrument_search(self, query):
        """جستجوی ابزار"""
        return None
    
    def get_usd_history(self, from_date, to_date):
        """دریافت تاریخچه دلار"""
        return None
    
    def get_sector_index_history(self, sector_code, from_date, to_date):
        """دریافت تاریخچه شاخص صنعت"""
        try:
            # تبدیل sector_code به string اگر float است
            sector_str = str(int(sector_code)) if isinstance(sector_code, float) else str(sector_code)
            url = f"{self.base_url}/tsev2/data/Index.aspx?i={sector_str}"
            response = self._make_request(url, timeout=10)
            return response if response else None
        except:
            return None
    
    def get_index_history(self, index_id, from_date, to_date):
        """دریافت تاریخچه شاخص"""
        try:
            url = f"{self.base_url}/tsev2/data/Index.aspx?i={index_id}"
            response = self._make_request(url, timeout=10)
            return response if response else None
        except:
            return None
    
    def parse_instrument_search(self, raw_data):
        """پارس نتایج جستجوی ابزار"""
        if not raw_data:
            return []
        # پیاده‌سازی ساده - باید بسته به فرمت واقعی TSE تکمیل شود
        return []
