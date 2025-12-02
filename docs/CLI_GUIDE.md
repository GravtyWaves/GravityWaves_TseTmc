# راهنمای حرفه‌ای CLI - TSE Data Collector

## نمای کلی

TSE Data Collector یک سیستم جمع‌آوری داده‌های بازار بورس تهران است که از طریق خط فرمان (CLI) قابل مدیریت است. این راهنما استفاده از ابزارهای CLI حرفه‌ای را توضیح می‌دهد.

## ابزارهای CLI موجود

### 1. `tse-cli` - ابزار اصلی مدیریت داده‌ها و PostgreSQL
ابزار اصلی برای مدیریت عملیات جمع‌آوری و به‌روزرسانی داده‌ها و عملیات پیشرفته PostgreSQL شامل پشتیبان‌گیری، بازیابی، بهینه‌سازی و اجرای کوئری.

### 2. `setup-postgresql` - ابزار راه‌اندازی PostgreSQL
ابزار حرفه‌ای برای نصب و راه‌اندازی کامل PostgreSQL.

---

## نصب و راه‌اندازی

### پیش‌نیازها

```bash
# نصب وابستگی‌های پایه
pip install -r requirements.txt

# برای PostgreSQL (اختیاری)
pip install psycopg2-binary python-dotenv
```

### راه‌اندازی سریع با SQLite (پیش‌فرض)

```bash
# راه‌اندازی کامل سیستم
tse-cli setup

# به‌روزرسانی داده‌ها
tse-cli update full
```

### راه‌اندازی با PostgreSQL

```bash
# 1. راه‌اندازی PostgreSQL
setup-postgresql --host localhost --port 5432 --user postgres --password your_password

# 2. تنظیم متغیرهای محیطی
# فایل .env به طور خودکار ایجاد می‌شود - آن را ویرایش کنید

# 3. راه‌اندازی سیستم
tse-cli setup --db-type postgresql

# 4. ایجاد ایندکس‌های عملکردی
tse-cli create-indexes

# 5. به‌روزرسانی داده‌ها
tse-cli update full
```

---

## دستورات tse-cli

### راه‌اندازی سیستم

```bash
# راه‌اندازی کامل با SQLite
tse-cli setup

# راه‌اندازی با PostgreSQL
tse-cli setup --db-type postgresql

# نمایش وضعیت سیستم
tse-cli status
```

### به‌روزرسانی داده‌ها

```bash
# جمع‌آوری داده‌های اولیه تازه از TSE API
tse-cli collect-initial

# به‌روزرسانی کامل همه داده‌ها
tse-cli update full

# به‌روزرسانی فقط سهام
tse-cli update stocks

# به‌روزرسانی فقط صنایع
tse-cli update sectors

# به‌روزرسانی فقط شاخص‌ها
tse-cli update indices

# به‌روزرسانی تاریخچه قیمت (30 روز اخیر)
tse-cli update prices

# به‌روزرسانی تاریخچه قیمت (90 روز اخیر)
tse-cli update prices --days 90

# به‌روزرسانی تاریخچه حقیقی-حقوقی
tse-cli update ri --days 90
```

### بازسازی جداول

```bash
# بازسازی جدول سهام (احتیاط - داده‌ها پاک می‌شوند)
tse-cli rebuild stocks

# بازسازی جدول قیمت‌ها
tse-cli rebuild price_history

# بازسازی با تایید خودکار
tse-cli rebuild stocks --force
```

### به‌روزرسانی مداوم

```bash
# اجرای به‌روزرسانی هر ساعت
tse-cli continuous --interval 3600

# اجرای به‌روزرسانی هر 30 دقیقه
tse-cli continuous --interval 1800
```

### گزینه‌های عمومی

```bash
# حالت verbose (جزئیات بیشتر)
tse-cli setup --verbose

# حالت dry-run (نمایش بدون اجرا)
tse-cli update full --dry-run

# حالت force (بدون تایید)
tse-cli rebuild stocks --force

# حالت quiet (خروجی کمتر)
tse-cli update full --quiet
```

---

### عملیات PostgreSQL

#### بررسی اتصال و وضعیت

```bash
# بررسی اتصال PostgreSQL
tse-cli check-connection

# نمایش اطلاعات دیتابیس
tse-cli db-info

# نمایش اطلاعات به صورت JSON
tse-cli db-info --format json
```

#### پشتیبان‌گیری و بازیابی

```bash
# پشتیبان‌گیری از دیتابیس
tse-cli backup backup_$(date +%Y%m%d_%H%M%S).dump

# پشتیبان‌گیری فشرده
tse-cli backup daily_backup.dump --compress

# بازیابی دیتابیس
tse-cli restore backup.dump

# بازیابی با تایید خودکار
tse-cli restore backup.dump --force
```

#### بهینه‌سازی عملکرد

```bash
# اجرای VACUUM ANALYZE
tse-cli optimize

# اجرای VACUUM FULL (برای آزادسازی فضا)
tse-cli optimize --full-vacuum

# ایجاد ایندکس‌های عملکردی
tse-cli create-indexes
```

#### اجرای کوئری‌های SQL

```bash
# نمایش تعداد کل سهام
tse-cli run-query "SELECT COUNT(*) FROM stocks"

# نمایش 5 سهم اول
tse-cli run-query "SELECT ticker, name FROM stocks LIMIT 5"

# کوئری پیشرفته با JOIN
tse-cli run-query "
SELECT s.ticker, s.name, COUNT(p.id) as price_records
FROM stocks s
LEFT JOIN price_history p ON s.id = p.stock_id
GROUP BY s.id, s.ticker, s.name
ORDER BY price_records DESC
LIMIT 10
"

# خروجی به صورت JSON
tse-cli run-query "SELECT * FROM stocks LIMIT 5" --format json

# محدود کردن تعداد نتایج
tse-cli run-query "SELECT * FROM price_history" --limit 100
```

#### تنظیم متغیرهای محیطی

```bash
# تنظیم متغیرهای محیطی
tse-cli setup-env
```

---

## دستورات setup-postgresql

### راه‌اندازی کامل PostgreSQL

```bash
# راه‌اندازی با تنظیمات پیش‌فرض
setup-postgresql

# راه‌اندازی با تنظیمات سفارشی
setup-postgresql --host localhost --port 5432 --user postgres --password mypassword --database tse_prod

# فقط نصب وابستگی‌های Python
setup-postgresql --no-create-db --no-env-file

# نمایش عملیات بدون اجرا
setup-postgresql --dry-run --verbose
```

### گزینه‌های setup-postgresql

```bash
# تنظیمات اتصال
--host HOST              PostgreSQL host (default: localhost)
--port PORT              PostgreSQL port (default: 5432)
--user USERNAME          PostgreSQL username (default: postgres)
--password PASSWORD      PostgreSQL password (default: password)
--database DB_NAME       Database name (default: tse_db)

# گزینه‌های راه‌اندازی
--no-install-deps        عدم نصب وابستگی‌های Python
--no-create-db          عدم ایجاد دیتابیس
--no-env-file           عدم ایجاد فایل .env

# گزینه‌های اجرایی
--verbose, -v           خروجی مفصل
--dry-run, -n          نمایش بدون اجرا
```

---

## سناریوهای عملی

### سناریوی 1: راه‌اندازی اولیه با SQLite

```bash
# 1. راه‌اندازی سیستم
tse-cli setup

# 2. بارگذاری داده‌های اولیه
tse-cli update full

# 3. بررسی وضعیت
tse-cli status
```

### سناریوی 2: راه‌اندازی کامل با PostgreSQL

```bash
# 1. راه‌اندازی PostgreSQL
setup-postgresql --user postgres --password secure_password

# 2. ویرایش فایل .env با اطلاعات صحیح

# 3. راه‌اندازی سیستم
tse-cli setup --db-type postgresql

# 4. ایجاد ایندکس‌ها
tse-cli create-indexes

# 5. به‌روزرسانی داده‌ها
tse-cli update full

# 6. پشتیبان‌گیری اولیه
tse-cli backup initial_backup.dump
```

### سناریوی 3: نگهداری روزانه

```bash
# به‌روزرسانی داده‌های روزانه
tse-cli update prices --days 1
tse-cli update ri --days 1

# بهینه‌سازی هفتگی
tse-cli optimize

# پشتیبان‌گیری روزانه
tse-cli backup daily_$(date +%Y%m%d).dump
```

### سناریوی 4: بازیابی از پشتیبان

```bash
# توقف سیستم اگر در حال اجرا است
# ...

# بازیابی از پشتیبان
postgres-cli restore daily_backup.dump

# بررسی یکپارچگی داده‌ها
postgres-cli info

# اجرای کوئری تأیید
postgres-cli query "SELECT COUNT(*) FROM stocks"
```

---

## عیب‌یابی

### مشکلات رایج اتصال به PostgreSQL

```bash
# بررسی اتصال
tse-cli check-connection

# اگر شکست خورد، بررسی متغیرهای محیطی
echo $DATABASE_URL

# یا بارگذاری مجدد فایل .env
tse-cli setup-env
```

### مشکلات عملکرد

```bash
# بررسی آمار دیتابیس
tse-cli db-info

# اجرای بهینه‌سازی
tse-cli optimize

# بررسی ایندکس‌ها
tse-cli run-query "
SELECT schemaname, tablename, indexname
FROM pg_indexes
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
"
```

### مشکلات حافظه یا فضای دیسک

```bash
# اجرای VACUUM FULL برای آزادسازی فضا
tse-cli optimize --full-vacuum

# بررسی فضای استفاده شده
tse-cli run-query "
SELECT schemaname, tablename,
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

---

## نکات امنیتی

1. **رمز عبور قوی**: از رمزهای عبور قوی برای PostgreSQL استفاده کنید
2. **متغیرهای محیطی**: فایل `.env` را در کنترل نسخه قرار ندهید
3. **پشتیبان‌گیری منظم**: پشتیبان‌گیری‌های منظم از داده‌ها داشته باشید
4. **دسترسی محدود**: دسترسی PostgreSQL را محدود به کاربران مجاز کنید
5. **مانیتورینگ**: لاگ‌ها را به طور منظم بررسی کنید

## راه‌اندازی اولیه PostgreSQL

```bash
# 1. تنظیم متغیر محیطی
set DATABASE_URL=postgresql://postgres:password@localhost:5432/tse_db

# 2. بررسی اتصال
tse-cli check-connection

# 3. ایجاد دیتابیس و جداول
tse-cli create-db

# 4. ایجاد ایندکس‌های عملکردی
tse-cli create-indexes

# 5. بارگذاری داده‌های اولیه
tse-cli update full
```

## پشتیبان‌گیری و بازیابی پیشرفته

```bash
# پشتیبان‌گیری فشرده
tse-cli backup daily_backup_$(date +%Y%m%d).dump --compress

# بازیابی با پاکسازی قبلی
tse-cli restore daily_backup_20231201.dump --clean

# پشتیبان‌گیری از جداول خاص
tse-cli backup stocks_backup.dump --tables stocks
```

## مانیتورینگ و نگهداری

```bash
# نمایش اطلاعات دیتابیس به صورت JSON
tse-cli db-info --format json

# بهینه‌سازی عملکرد هفتگی
tse-cli optimize

# اجرای کوئری‌های تحلیلی
tse-cli run-query "SELECT COUNT(*) as total_stocks FROM stocks"
tse-cli run-query "SELECT COUNT(*) as total_prices FROM price_history"
tse-cli run-query "SELECT ticker, COUNT(*) as price_records FROM stocks s JOIN price_history p ON s.id = p.stock_id GROUP BY s.id, s.ticker ORDER BY price_records DESC LIMIT 10"
```

## لیست کامل دستورات PostgreSQL

| دستور | توضیح |
|-------|--------|
| `check-connection` | بررسی اتصال به PostgreSQL |
| `create-db` | ایجاد دیتابیس و جداول |
| `drop-db` | حذف تمام جداول (با تأیید) |
| `backup <file>` | پشتیبان‌گیری از دیتابیس |
| `restore <file>` | بازیابی دیتابیس از پشتیبان |
| `db-info` | نمایش اطلاعات دیتابیس |
| `optimize` | بهینه‌سازی عملکرد دیتابیس |
| `create-indexes` | ایجاد ایندکس‌های عملکردی |
| `run-query "<sql>"` | اجرای کوئری SQL سفارشی |
| `setup-env` | تنظیم متغیرهای محیطی |

## نکات مهم PostgreSQL

1. **متغیر محیطی DATABASE_URL** باید قبل از استفاده از دستورات تنظیم شود
2. **پشتیبان‌گیری منظم** از داده‌ها قبل از عملیات مهم توصیه می‌شود
3. **دستور drop-db** تمام داده‌ها را پاک می‌کند - با احتیاط استفاده کنید
4. **ایندکس‌ها** برای بهبود عملکرد کوئری‌ها ضروری هستند
5. **بهینه‌سازی** باید به صورت دوره‌ای انجام شود

## عیب‌یابی پیشرفته PostgreSQL

### خطای اتصال
```
Error: PostgreSQL connection failed
```
- متغیر `DATABASE_URL` را بررسی کنید
- مطمئن شوید PostgreSQL اجرا شده است
- تنظیمات firewall را بررسی کنید

### خطای پشتیبان‌گیری
```
Backup failed: pg_dump not found
```
- مطمئن شوید PostgreSQL client tools نصب شده است
- PATH سیستم را بررسی کنید

### خطای بازیابی
```
Restore failed: permission denied
```
- دسترسی کاربر PostgreSQL را بررسی کنید
- مطمئن شوید دیتابیس خالی است یا از `--clean` استفاده کنید

## پشتیبانی

برای دریافت کمک بیشتر:

- بررسی لاگ‌های سیستم در: `tse_collector.log`
- اجرای تست‌ها: `python -m pytest tests/`

---

*این راهنما برای TSE Data Collector نسخه 2.0 نوشته شده است.*
