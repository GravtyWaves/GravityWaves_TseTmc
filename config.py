# مسیرهای ذخیره‌سازی داده‌ها
DATA_PATH = 'D:/FinPy-TSE Data/'
PRICE_PANEL_PATH = DATA_PATH + 'Price Panel/'
MARKETWATCH_PATH = DATA_PATH + 'MarketWatch/'

# اندازه سگمنت برای پردازش دسته‌ای
SEGMENT_SIZE = 25

# هدرهای درخواست HTTP
DEFAULT_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
}

# لیست بازارهای مجاز
MARKET_ID_LIST = ['300','303','305','309','400','403','404']

# سایر تنظیمات قابل ویرایش را اینجا اضافه کنید
import os
from pathlib import Path

# مسیر پروژه
BASE_DIR = Path(__file__).parent

# تنظیمات دیتابیس
DATABASE_TYPE = os.getenv("DATABASE_TYPE", "sqlite")  # sqlite یا postgresql

if DATABASE_TYPE == "sqlite":
    DATABASE_URL = f"sqlite:///{BASE_DIR}/tse_data.db"
elif DATABASE_TYPE == "postgresql":
    DATABASE_URL = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:password@localhost:5432/tse_db"
    )

# تنظیمات API
API_BASE_URL = "https://www.tsetmc.com/tsev2/data"
API_TIMEOUT = 30  # ثانیه
MAX_RETRIES = 3
RETRY_DELAY = 1  # ثانیه

# تنظیمات به‌روزرسانی
UPDATE_INTERVAL = 24 * 60 * 60  # 24 ساعت به ثانیه
BATCH_SIZE = 100  # تعداد رکوردها در هر بار درج

# تنظیمات لاگینگ
LOG_LEVEL = "INFO"
LOG_FILE = f"{BASE_DIR}/tse_collector.log"

# مسیر فایل‌های داده اولیه
SECTORS_DATA_FILE = f"{BASE_DIR}/data/sectors.json"

# تنظیمات PostgreSQL
POSTGRES_CONFIG = {
    "pool_size": 10,
    "max_overflow": 20,
    "pool_pre_ping": True,
    "pool_recycle": 3600,
}
