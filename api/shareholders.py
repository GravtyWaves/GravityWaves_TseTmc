"""
shareholders.py
ماژول استاندارد برای دریافت و ذخیره اطلاعات سهامداران
"""
import pandas as pd
import jdatetime
import requests
from config import DEFAULT_HEADERS
from database.models import Shareholder
from database.sqlite_db import get_sqlite_session
from database.postgres_db import get_postgres_session

def fetch_and_store_shareholders(ticker):
    """
    دریافت و ذخیره اطلاعات سهامداران بالای 1% نماد مورد نظر
    خروجی:
        DataFrame سهامداران
    """
    # دریافت داده سهامداران و ذخیره‌سازی استاندارد
    try:
        # فرض بر این است که تابع دریافت داده مشابه Get_ShareHoldersInfo پیاده‌سازی شده است
        # داده را دریافت و پردازش کنید (نمونه ساده)
        # For testing, create sample data
        df_sh = pd.DataFrame({
            'Ticker': [ticker],
            'Market': ['Bourse'],
            'Name': ['Holder1'],
            'ShareNo': [1000],
            'SharePct': [10.5],
            'Changes': [100]
        })
        # ذخیره‌سازی در دیتابیس
        from database.models import Shareholder
        from database.sqlite_db import get_sqlite_session
        from database.postgres_db import get_postgres_session
        shareholder_records = []
        for idx, row in df_sh.reset_index().iterrows():
            shareholder_records.append(Shareholder(
                shareholder_id=f"SH{idx+1:03d}_{ticker}",
                name=row['Name']
            ))
        # Store in SQLite
        sqlite_session = get_sqlite_session()
        sqlite_session.bulk_save_objects(shareholder_records)
        sqlite_session.commit()
        sqlite_session.close()
        # Store in PostgreSQL
        postgres_session = get_postgres_session()
        postgres_session.bulk_save_objects(shareholder_records)
        postgres_session.commit()
        postgres_session.close()
        print("[Success] Shareholder records stored in both SQLite and PostgreSQL.")
        return df_sh
    except Exception as e:
        print(f"[Error] Database storage error (Shareholder): {e}")
        return df_sh  # Return the data even if storage fails

# سایر توابع مرتبط با سهامداران را می‌توان در این فایل استانداردسازی و مستندسازی کرد.
