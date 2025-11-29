import re
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def clean_persian_text(text: str) -> str:
    """پاکسازی متن فارسی از کاراکترهای غیرضروری"""
    if not text:
        return ""
    
    # حذف کاراکترهای کنترل
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    
    # نرمال‌سازی فاصله‌ها
    text = re.sub(r'\s+', ' ', text.strip())
    
    return text

def normalize_ticker(ticker: str) -> str:
    """نرمال‌سازی تیکر سهام"""
    if not ticker:
        return ""
    
    # حذف کاراکترهای غیرمجاز
    ticker = re.sub(r'[^a-zA-Z0-9]', '', ticker.upper())
    
    return ticker

def parse_jalali_date(date_str: str) -> Optional[datetime]:
    """تبدیل تاریخ شمسی به میلادی"""
    try:
        # فرمت: YYYY/MM/DD
        parts = date_str.split('/')
        if len(parts) != 3:
            return None
            
        jy, jm, jd = map(int, parts)
        
        # تبدیل تقریبی شمسی به میلادی
        gy = jy + 621
        if jm > 3 or (jm == 3 and jd >= 21):
            gy += 1
            
        # ایجاد تاریخ میلادی
        return datetime(gy, jm, jd)
        
    except (ValueError, IndexError):
        logger.warning(f"Invalid Jalali date format: {date_str}")
        return None

def format_jalali_date(date: datetime) -> str:
    """تبدیل تاریخ میلادی به شمسی"""
    # تبدیل تقریبی میلادی به شمسی
    gy, gm, gd = date.year, date.month, date.day

    jy = gy - 621
    if gm < 3 or (gm == 3 and gd < 21):
        jy -= 1

    return f"{jy:04d}/{gm:02d}/{gd:02d}"

def validate_web_id(web_id: str) -> bool:
    """اعتبارسنجی web_id"""
    if not web_id:
        return False
    
    # web_id باید عددی باشد
    try:
        int(web_id)
        return True
    except ValueError:
        return False

def validate_sector_code(sector_code: float) -> bool:
    """اعتبارسنجی کد صنعت"""
    try:
        code = float(sector_code)
        return code > 0
    except (ValueError, TypeError):
        return False

def safe_float_convert(value: Any) -> Optional[float]:
    """تبدیل امن به float"""
    if value is None or value == "":
        return None
    
    try:
        if isinstance(value, str):
            # حذف کاما و تبدیل
            value = value.replace(',', '')
        return float(value)
    except (ValueError, TypeError):
        return None

def safe_int_convert(value: Any) -> Optional[int]:
    """تبدیل امن به int"""
    if value is None or value == "":
        return None

    try:
        if isinstance(value, str):
            # حذف کاما و تبدیل
            value = value.replace(',', '')
        # فقط اگر مقدار دقیقاً integer باشد تبدیل کن
        float_val = float(value)
        if float_val == int(float_val):
            return int(float_val)
        else:
            return None  # اگر decimal دارد None برگردان
    except (ValueError, TypeError):
        return None

def calculate_percentage_change(old_value: float, new_value: float) -> Optional[float]:
    """محاسبه درصد تغییر"""
    if old_value == 0:
        return None
    
    try:
        return ((new_value - old_value) / old_value) * 100
    except (ZeroDivisionError, TypeError):
        return None

def group_data_by_date(data: List[Dict[str, Any]], date_field: str = 'date') -> Dict[str, List[Dict[str, Any]]]:
    """گروه‌بندی داده‌ها بر اساس تاریخ"""
    grouped = {}
    
    for item in data:
        date = item.get(date_field)
        if date:
            if date not in grouped:
                grouped[date] = []
            grouped[date].append(item)
    
    return grouped

def filter_data_by_date_range(data: List[Dict[str, Any]], 
                             from_date: str, 
                             to_date: str, 
                             date_field: str = 'date') -> List[Dict[str, Any]]:
    """فیلتر داده‌ها بر اساس بازه زمانی"""
    filtered = []
    
    from_dt = parse_jalali_date(from_date)
    to_dt = parse_jalali_date(to_date)
    
    if not from_dt or not to_dt:
        return data
    
    for item in data:
        item_date_str = item.get(date_field)
        if item_date_str:
            item_dt = parse_jalali_date(item_date_str)
            if item_dt and from_dt <= item_dt <= to_dt:
                filtered.append(item)
    
    return filtered

def calculate_moving_average(data: List[float], window: int = 5) -> List[Optional[float]]:
    """محاسبه میانگین متحرک"""
    if len(data) < window:
        return [None] * len(data)
    
    result = []
    for i in range(len(data)):
        if i < window - 1:
            result.append(None)
        else:
            window_data = data[i-window+1:i+1]
            avg = sum(window_data) / len(window_data)
            result.append(avg)
    
    return result

def detect_outliers(data: List[float], threshold: float = 2.0) -> List[bool]:
    """تشخیص داده‌های پرت با استفاده از Z-score"""
    if len(data) < 2:
        return [False] * len(data)
    
    mean = sum(data) / len(data)
    variance = sum((x - mean) ** 2 for x in data) / len(data)
    std_dev = variance ** 0.5
    
    if std_dev == 0:
        return [False] * len(data)
    
    outliers = []
    for value in data:
        z_score = abs(value - mean) / std_dev
        outliers.append(z_score > threshold)
    
    return outliers

def save_json_to_file(data: Any, file_path: str) -> bool:
    """ذخیره داده‌ها در فایل JSON"""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving JSON to {file_path}: {e}")
        return False

def load_json_from_file(file_path: str) -> Optional[Any]:
    """بارگذاری داده‌ها از فایل JSON"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading JSON from {file_path}: {e}")
        return None

def chunk_list(data: List[Any], chunk_size: int) -> List[List[Any]]:
    """تقسیم لیست به چانک‌های کوچک‌تر"""
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]

def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """ادغام دیکشنری‌ها"""
    result = {}
    for d in dicts:
        result.update(d)
    return result

def get_nested_value(data: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    """دریافت مقدار تودرتو از دیکشنری"""
    current = data
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current
