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
        "postgresql://user:password@localhost/tse_db"
    )

# تنظیمات API
API_BASE_URL = "http://www.tsetmc.com/tsev2/data"
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
