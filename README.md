# TSE Data Collector

یک ابزار جامع برای جمع‌آوری و ذخیره‌سازی داده‌های بازار بورس تهران (TSE) شامل قیمت‌ها، شاخص‌ها، معاملات و اطلاعات شرکت‌ها.

## ویژگی‌ها

- **جمع‌آوری داده‌های لحظه‌ای**: دریافت اطلاعات زنده از API بورس تهران
- **پایگاه داده محلی**: ذخیره‌سازی داده‌ها در SQLite با استفاده از SQLAlchemy
- **تاریخچه کامل**: ذخیره قیمت‌ها، معاملات حقیقی-حقوقی، شاخص‌ها و داده‌های صنایع
- **به‌روزرسانی خودکار**: امکان اجرای مداوم برای جمع‌آوری داده‌های جدید
- **لاگ‌گیری کامل**: ثبت تمامی عملیات و خطاها
- **API کاربرپسند**: رابط برنامه‌نویسی ساده برای توسعه‌دهندگان

## ساختار پروژه

```
tse_collector/
├── config.py              # تنظیمات برنامه
├── main.py                # نقطه ورود اصلی
├── requirements.txt       # وابستگی‌های Python
├── database/
│   ├── __init__.py
│   ├── base.py           # کلاس پایه دیتابیس
│   ├── models.py         # مدل‌های SQLAlchemy
│   └── sqlite_db.py      # پیاده‌سازی SQLite
├── api/
│   ├── __init__.py
│   ├── tse_api.py        # کلاینت API بورس
│   └── ...
├── utils/
│   ├── __init__.py
│   ├── logger.py         # ابزارهای لاگ‌گیری
│   └── helpers.py        # توابع کمکی
└── data/
    └── sectors.json      # داده‌های اولیه صنایع
```

## پیش‌نیازها

- Python 3.8+
- دسترسی به اینترنت برای دریافت داده‌ها از API بورس

## نصب و راه‌اندازی

1. **کلون کردن پروژه**:
```bash
git clone <repository-url>
cd tse_collector
```

2. **نصب وابستگی‌ها**:
```bash
pip install -r requirements.txt
```

3. **تنظیم متغیرهای محیطی (اختیاری)**:
```bash
export DATABASE_TYPE=sqlite  # یا postgresql
export DATABASE_URL=postgresql://user:password@localhost/tse_db
```

4. **اجرای برنامه**:
```bash
# اجرای کامل (جمع‌آوری همه داده‌ها)
python main.py --mode full

# اجرای مداوم (به‌روزرسانی هر 24 ساعت)
python main.py --mode continuous

# جمع‌آوری فقط سهام
python main.py --mode stocks

# به‌روزرسانی قیمت‌ها برای 30 روز گذشته
python main.py --mode prices --days 30
```

## استفاده از API

```python
from api.tse_api import TSEAPIClient
from database.sqlite_db import SQLiteDatabase

# اتصال به API
api = TSEAPIClient()

# دریافت لیست سهام
stocks = api.get_stock_list()

# دریافت تاریخچه قیمت
prices = api.get_price_history('web_id', '1400/01/01', '1400/12/29')

# اتصال به دیتابیس
db = SQLiteDatabase()

# ذخیره داده‌ها
db.add_stock({'ticker': 'ABC', 'name': 'شرکت نمونه', ...})
```

## مدل‌های داده

### Stock (سهام)
- اطلاعات پایه شرکت شامل نام، نماد، کد وب و صنعت

### PriceHistory (تاریخچه قیمت)
- قیمت‌های روزانه شامل باز، بسته، کمینه، بیشینه، حجم و ارزش معاملات

### RIHistory (تاریخچه حقیقی-حقوقی)
- معاملات روزانه بر اساس نوع سرمایه‌گذار (حقیقی/حقوقی)

### Index (شاخص)
- شاخص‌های بازار بورس تهران

### Sector (صنعت)
- اطلاعات صنایع و گروه‌بندی شرکت‌ها

## تنظیمات

فایل `config.py` شامل تنظیمات زیر است:

- `DATABASE_URL`: آدرس پایگاه داده
- `API_BASE_URL`: آدرس API بورس
- `UPDATE_INTERVAL`: فاصله زمانی به‌روزرسانی (ثانیه)
- `LOG_LEVEL`: سطح لاگ‌گیری
- `BATCH_SIZE`: اندازه دسته‌های درج داده

## لاگ‌گیری

تمامی عملیات در فایل `tse_collector.log` ثبت می‌شود. سطوح لاگ:

- `DEBUG`: اطلاعات جزئی عملیات
- `INFO`: اطلاعات کلی پیشرفت
- `WARNING`: هشدارها
- `ERROR`: خطاها

## تست و توسعه

```bash
# اجرای تست‌ها
python -m pytest

# بررسی پوشش کد
python -m pytest --cov=tse_collector

# اجرای با تنظیمات توسعه
python main.py --mode full --days 1
```

## خطاها و مشکلات رایج

### خطای اتصال به API
- بررسی اتصال اینترنت
- تأیید دسترسی به `http://cdn.tsetmc.com`

### خطای دیتابیس
- بررسی وجود فایل دیتابیس
- تأیید مجوزهای نوشتن

### خطای حافظه
- کاهش `BATCH_SIZE` در تنظیمات
- اجرای به‌روزرسانی در بازه‌های زمانی کوچکتر

## مشارکت

1. Fork پروژه
2. ایجاد branch جدید (`git checkout -b feature/AmazingFeature`)
3. Commit تغییرات (`git commit -m 'Add some AmazingFeature'`)
4. Push به branch (`git push origin feature/AmazingFeature`)
5. ایجاد Pull Request

## لایسنس

این پروژه تحت لایسنس MIT منتشر شده است.

## تماس

برای سوالات و پیشنهادات:
- ایمیل: your-email@example.com
- گیت‌هاب: [GitHub Issues](https://github.com/yourusername/tse_collector/issues)
