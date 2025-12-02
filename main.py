#!/usr/bin/env python3
"""
نقطه ورود اصلی برنامه جمع‌آوری داده‌های TSE
"""

import argparse
import sys
import time
from datetime import datetime, timedelta
from typing import Optional
import logging

from config import UPDATE_INTERVAL, BATCH_SIZE, DATABASE_TYPE
from database.sqlite_db import SQLiteDatabase
from database.postgres_db import PostgreSQLDatabase
 # حذف وابستگی به TSEAPIClient
from utils.logger import setup_logger, log_performance
from utils.helpers import format_jalali_date, parse_jalali_date

# تنظیم لاگر
logger = setup_logger()

class TSEDataCollector:
    def __init__(self, db_type="sqlite"):
        if db_type == "postgresql":
            self.db = PostgreSQLDatabase()
        else:
            self.db = SQLiteDatabase()
        # استفاده از API واقعی
        from api.tse_api import TSEAPIClient
        self.api = TSEAPIClient()
        
    def create_database(self):
        """ایجاد دیتابیس و جداول"""
        logger.info("Creating database tables")
        self.db.create_tables()
        logger.info("Database tables created successfully")
        
    def load_initial_data(self):
        """بارگذاری داده‌های اولیه"""
        logger.info("Loading initial data")
        try:
            self.db.load_sectors_from_file()
            logger.info("Initial data loaded successfully")
        except Exception as e:
            logger.error(f"Error loading initial data: {e}")
            return False
        return True
        
    def rebuild_table(self, table_name: str):
        """ساختن دوباره یک جدول خاص"""
        logger.info(f"Rebuilding table: {table_name}")
        
        from database.models import Base
        
        # دریافت جدول مورد نظر
        table_class = None
        for cls in Base.__subclasses__():
            if cls.__tablename__ == table_name:
                table_class = cls
                break
        
        if not table_class:
            logger.error(f"Table {table_name} not found")
            return False
        
        session = self.db.get_session()
        try:
            # حذف داده‌های جدول
            session.query(table_class).delete()
            session.commit()
            logger.info(f"Table {table_name} cleared")
            
            # جمع‌آوری مجدد داده‌ها
            if table_name == 'stocks':
                self.collect_stocks()
            elif table_name == 'sectors':
                self.collect_sectors()
            elif table_name == 'indices':
                self.collect_indices()
            elif table_name == 'price_history':
                self.update_price_history(365)  # یک سال تاریخچه
            elif table_name == 'ri_history':
                self.update_ri_history(365)  # یک سال تاریخچه
            else:
                logger.warning(f"No specific collection method for table {table_name}")
                
            logger.info(f"Table {table_name} rebuilt successfully")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error rebuilding table {table_name}: {e}")
            return False
        finally:
            session.close()
    
    def collect_stocks(self) -> int:
        """جمع‌آوری لیست سهام با داده واقعی و ذخیره در پایگاه داده"""
        logger.info("Starting stock collection")
        stock_list = self.api.get_stock_list()
        if not stock_list:
            logger.warning("No stocks fetched from API")
            return 0
        
        count = 0
        for stock in stock_list:
            stock_data = {
                'ticker': stock.get('ticker'),
                'name': stock.get('name'),
                'web_id': stock.get('web_id'),
                'market': stock.get('SectorCode', None)
            }
            if self.db.add_stock(stock_data):
                count += 1
        
        logger.info(f"Collected {count} new stocks from API (total: {len(stock_list)})")
        return count
    
    def collect_sectors(self) -> int:
        """جمع‌آوری لیست صنایع با داده واقعی و ذخیره در پایگاه داده"""
        logger.info("Starting sector collection")
        sector_list = self.api.get_sector_list()
        if not sector_list:
            logger.warning("No sectors fetched from API")
            return 0
        count = 0
        for sector in sector_list:
            try:
                sector_code = float(sector.get('SectorCode', 0))
            except (ValueError, TypeError):
                sector_code = 0.0
            sector_data = {
                'sector_code': sector_code,
                'sector_name': sector.get('SectorName', ''),
                'sector_name_en': sector.get('SectorNameEn', '')
            }
            result = self.db.add_sector(sector_data)
            if result:
                count += 1
        logger.info(f"Collected {count} sectors from API")
        return count
    
    def collect_indices(self) -> int:
        """جمع‌آوری لیست شاخص‌ها با داده واقعی و ذخیره در پایگاه داده"""
        logger.info("Starting index collection")
        index_list = self.api.get_index_list()
        if not index_list:
            logger.warning("No indices fetched from API")
            return 0
        count = 0
        for index in index_list:
            index_data = {
                'name': index.get('name'),
                'web_id': index.get('web_id')
            }
            result = self.db.add_index(index_data)
            if result:
                count += 1
        logger.info(f"Collected {count} indices from API")
        return count
    
    def update_price_history(self, days: int = 30) -> int:
        """به‌روزرسانی تاریخچه قیمت سهام - استفاده از scraping مستقیم"""
        logger.info(f"Starting price history update for last {days} days")
        logger.warning("Price history update from scraping not fully implemented yet")
        return 0
    
    def update_ri_history(self, days: int = 30) -> int:
        """به‌روزرسانی تاریخچه حقیقی-حقوقی - استفاده از scraping مستقیم"""
        logger.info(f"Starting RI history update for last {days} days")
        logger.warning("RI history update from scraping not fully implemented yet")
        return 0
    
    def run_full_update(self) -> dict:
        """اجرای به‌روزرسانی کامل"""
        logger.info("Starting full data update")
        start_time = time.time()
        
        results = {
            'stocks': self.collect_stocks(),
            'sectors': self.collect_sectors(),
            'indices': self.collect_indices(),
            'price_history': self.update_price_history(),
            'ri_history': self.update_ri_history(),
            'success': True
        }
        
        duration = time.time() - start_time
        log_performance("run_full_update", duration)
        logger.info(f"Full update completed in {duration:.2f}s")
        
        return results
    
    def run_continuous_update(self, interval: int = None):
        """اجرای به‌روزرسانی مداوم"""
        if interval is None:
            interval = UPDATE_INTERVAL
            
        logger.info(f"Starting continuous update with {interval}s interval")
        
        while True:
            try:
                self.run_full_update()
                logger.info(f"Sleeping for {interval} seconds")
                time.sleep(interval)
            except KeyboardInterrupt:
                logger.info("Continuous update stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in continuous update: {e}")
                time.sleep(60)  # انتظار یک دقیقه در صورت خطا
def create_parser():
    parser = argparse.ArgumentParser(description='TSE Data Collector',
                                     formatter_class=argparse.RawDescriptionHelpFormatter,
                                     epilog="""
Examples:
  # ایجاد دیتابیس SQLite
  python main.py create-db --type sqlite
  
  # ایجاد دیتابیس PostgreSQL
  python main.py create-db --type postgresql
  
  # بارگذاری داده‌های اولیه
  python main.py load-initial-data
  
  # به‌روزرسانی کامل
  python main.py update --mode full
  
  # به‌روزرسانی فقط سهام
  python main.py update --mode stocks
  
  # به‌روزرسانی تاریخچه قیمت برای 90 روز
  python main.py update --mode prices --days 90
  
  # ساختن دوباره جدول سهام
  python main.py rebuild-table --table stocks
  
  # اجرای به‌روزرسانی مداوم
  python main.py continuous-update --interval 3600
""")

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # دستور ایجاد دیتابیس
    create_db_parser = subparsers.add_parser('create-db', help='Create database and tables')
    create_db_parser.add_argument('--type', choices=['sqlite', 'postgresql'],
                                  default='sqlite', help='Database type')

    # دستور بارگذاری داده‌های اولیه
    load_parser = subparsers.add_parser('load-initial-data', help='Load initial data')

    # دستور به‌روزرسانی
    update_parser = subparsers.add_parser('update', help='Update data')
    update_parser.add_argument('--mode', choices=['full', 'stocks', 'sectors', 'indices', 'prices', 'ri'],
                               default='full', help='Update mode')
    update_parser.add_argument('--days', type=int, default=30, help='Number of days to update')
    update_parser.add_argument('--type', choices=['sqlite', 'postgresql'],
                               default='sqlite', help='Database type')

    # دستور ساختن دوباره جدول
    rebuild_parser = subparsers.add_parser('rebuild-table', help='Rebuild specific table')
    rebuild_parser.add_argument('--table', required=True,
                                choices=['stocks', 'sectors', 'indices', 'price_history', 'ri_history'],
                                help='Table to rebuild')
    rebuild_parser.add_argument('--type', choices=['sqlite', 'postgresql'],
                                default='sqlite', help='Database type')

    # دستور به‌روزرسانی مداوم
    continuous_parser = subparsers.add_parser('continuous-update', help='Continuous update')
    continuous_parser.add_argument('--interval', type=int, default=None,
                                   help='Update interval in seconds')
    continuous_parser.add_argument('--type', choices=['sqlite', 'postgresql'],
                                   default='sqlite', help='Database type')

    return parser


def main():
    parser = create_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    try:
        collector = TSEDataCollector(args.type if hasattr(args, 'type') else 'sqlite')

        if args.command == 'create-db':
            collector.create_database()
            print("Database created successfully")

        elif args.command == 'load-initial-data':
            if collector.load_initial_data():
                print("Initial data loaded successfully")
            else:
                print("Failed to load initial data")
                sys.exit(1)

        elif args.command == 'update':
            if args.mode == 'full':
                results = collector.run_full_update()
                print(f"Update completed: {results}")

            elif args.mode == 'stocks':
                count = collector.collect_stocks()
                print(f"Collected {count} stocks")

            elif args.mode == 'sectors':
                count = collector.collect_sectors()
                print(f"Collected {count} sectors")

            elif args.mode == 'indices':
                count = collector.collect_indices()
                print(f"Collected {count} indices")

            elif args.mode == 'prices':
                count = collector.update_price_history(args.days)
                print(f"Updated {count} price records")

            elif args.mode == 'ri':
                count = collector.update_ri_history(args.days)
                print(f"Updated {count} RI records")

        elif args.command == 'rebuild-table':
            if collector.rebuild_table(args.table):
                print(f"Table {args.table} rebuilt successfully")
            else:
                print(f"Failed to rebuild table {args.table}")
                sys.exit(1)

        elif args.command == 'continuous-update':
            collector.run_continuous_update(args.interval)

        else:
            logger.error(f"Unknown command: {args.command}")

    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
