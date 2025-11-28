import logging
import time
from functools import wraps
from typing import Any, Callable
from pathlib import Path

from config import LOG_LEVEL, LOG_FILE

def setup_logger(name: str = "tse_collector") -> logging.Logger:
    """تنظیم لاگر برنامه"""
    # تبدیل سطح لاگ به عدد
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    level = level_map.get(LOG_LEVEL.upper(), logging.INFO)
    
    # تنظیم فرمت لاگ
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # تنظیم handler کنسول
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    
    # تنظیم handler فایل
    log_path = Path(LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    
    # تنظیم لاگر
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # پاک کردن handlerهای قبلی
    logger.handlers.clear()
    
    # اضافه کردن handlerها
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

def log_performance(func_name: str, duration: float, records_processed: int = None) -> None:
    """لاگ عملکرد عملیات"""
    logger = logging.getLogger("tse_collector")
    
    if records_processed is not None:
        records_per_second = records_processed / duration if duration > 0 else 0
        logger.info(
            f"Performance: {func_name} - Duration: {duration:.2f}s, "
            f"Records: {records_processed}, Rate: {records_per_second:.2f} rec/s"
        )
    else:
        logger.info(f"Performance: {func_name} - Duration: {duration:.2f}s")

def performance_logger(func: Callable) -> Callable:
    """دکوراتور برای لاگ عملکرد توابع"""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        logger = logging.getLogger("tse_collector")
        logger.debug(f"Starting {func.__name__}")
        
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            log_performance(func.__name__, duration)
            logger.debug(f"Completed {func.__name__}")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"Error in {func.__name__} after {duration:.2f}s: {e}")
            raise
    
    return wrapper

def log_api_call(endpoint: str, params: dict = None, success: bool = True, duration: float = None) -> None:
    """لاگ فراخوانی API"""
    logger = logging.getLogger("tse_collector")
    
    if success:
        if duration is not None:
            logger.debug(f"API call successful: {endpoint} ({duration:.2f}s)")
        else:
            logger.debug(f"API call successful: {endpoint}")
    else:
        logger.warning(f"API call failed: {endpoint}")
        if params:
            logger.debug(f"Parameters: {params}")

def log_database_operation(operation: str, table: str, records: int = None, success: bool = True) -> None:
    """لاگ عملیات دیتابیس"""
    logger = logging.getLogger("tse_collector")
    
    if success:
        if records is not None:
            logger.debug(f"DB operation successful: {operation} on {table} ({records} records)")
        else:
            logger.debug(f"DB operation successful: {operation} on {table}")
    else:
        logger.error(f"DB operation failed: {operation} on {table}")

def setup_request_logging() -> None:
    """تنظیم لاگ درخواست‌های HTTP"""
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
