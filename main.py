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

from config import UPDATE_INTERVAL, BATCH_SIZE
from database.sqlite_db import SQLiteDatabase
from api.tse_api import TSEAPIClient
from utils.logger import setup_logger, log_performance
from utils.helpers import format_jalali_date, parse_jalali_date

# تنظیم لاگر
logger = setup_logger()

class TSEDataCollector:
    def __init__(self):
        self.db = SQLiteDatabase()
        self.api = TSEAPIClient()
        
    def collect_stocks(self) -> int:
        """جمع‌آوری لیست سهام"""
        logger.info("Starting stock collection")
        start_time = time.time()
        
        try:
            stock_list = self.api.get_stock_list()
            if not stock_list:
                logger.error("Failed to fetch stock list")
                return 0
            
            collected_count = 0
            for stock_data in stock_list:
                # تبدیل داده‌های API به فرمت دیتابیس
                db_stock = {
                    'ticker': stock_data.get('Symbol', ''),
                    'name': stock_data.get('CompanyName', ''),
                    'name_en': stock_data.get('CompanyNameEn', ''),
                    'web_id': str(stock_data.get('InsCode', '')),
                    'sector_code': stock_data.get('SectorCode', 0.0)
                }
                
                if self.db.add_stock(db_stock):
                    collected_count += 1
            
            duration = time.time() - start_time
            log_performance("collect_stocks", duration, collected_count)
            logger.info(f"Collected {collected_count} stocks")
            return collected_count
            
        except Exception as e:
            logger.error(f"Error collecting stocks: {e}")
            return 0
    
    def collect_sectors(self) -> int:
        """جمع‌آوری لیست صنایع"""
        logger.info("Starting sector collection")
        start_time = time.time()
        
        try:
            sector_list = self.api.get_sector_list()
            if not sector_list:
                logger.error("Failed to fetch sector list")
                return 0
            
            collected_count = 0
            for sector_data in sector_list:
                # تبدیل داده‌های API به فرمت دیتابیس
                db_sector = {
                    'sector_code': sector_data.get('SectorCode', 0.0),
                    'sector_name': sector_data.get('SectorName', ''),
                    'sector_name_en': sector_data.get('SectorNameEn', ''),
                    'naics_code': sector_data.get('NAICSCode', ''),
                    'naics_name': sector_data.get('NAICSName', '')
                }
                
                # بررسی وجود صنعت
                existing = self.db.get_sector_by_code(db_sector['sector_code'])
                if not existing:
                    # درج صنعت جدید
                    from database.models import Sector
                    sector = Sector(**db_sector)
                    session = self.db.get_session()
                    try:
                        session.add(sector)
                        session.commit()
                        collected_count += 1
                    except Exception as e:
                        session.rollback()
                        logger.error(f"Error adding sector {db_sector['sector_code']}: {e}")
                    finally:
                        session.close()
            
            duration = time.time() - start_time
            log_performance("collect_sectors", duration, collected_count)
            logger.info(f"Collected {collected_count} sectors")
            return collected_count
            
        except Exception as e:
            logger.error(f"Error collecting sectors: {e}")
            return 0
    
    def collect_indices(self) -> int:
        """جمع‌آوری لیست شاخص‌ها"""
        logger.info("Starting index collection")
        start_time = time.time()
        
        try:
            index_list = self.api.get_index_list()
            if not index_list:
                logger.error("Failed to fetch index list")
                return 0
            
            collected_count = 0
            for index_data in index_list:
                # تبدیل داده‌های API به فرمت دیتابیس
                db_index = {
                    'name': index_data.get('IndexName', ''),
                    'name_en': index_data.get('IndexNameEn', ''),
                    'web_id': str(index_data.get('InsCode', ''))
                }
                
                if self.db.add_index(db_index):
                    collected_count += 1
            
            duration = time.time() - start_time
            log_performance("collect_indices", duration, collected_count)
            logger.info(f"Collected {collected_count} indices")
            return collected_count
            
        except Exception as e:
            logger.error(f"Error collecting indices: {e}")
            return 0
    
    def update_price_history(self, days: int = 30) -> int:
        """به‌روزرسانی تاریخچه قیمت سهام"""
        logger.info(f"Starting price history update for last {days} days")
        start_time = time.time()
        
        try:
            from_date, to_date = self.api.get_date_range(days)
            
            # دریافت لیست سهام
            session = self.db.get_session()
            stocks = session.query(self.db.Stock).all()
            session.close()
            
            total_updated = 0
            for stock in stocks:
                try:
                    # بررسی آخرین تاریخ قیمت
                    last_date = self.db.get_last_price_date(stock.id)
                    
                    if last_date:
                        # فقط داده‌های جدید را دریافت کنیم
                        last_dt = parse_jalali_date(last_date)
                        if last_dt:
                            from_dt = last_dt + timedelta(days=1)
                            from_date = format_jalali_date(from_dt)
                    
                    # دریافت تاریخچه قیمت
                    history = self.api.get_price_history(stock.web_id, from_date, to_date)
                    if history:
                        # تبدیل به فرمت دیتابیس
                        db_history = []
                        for item in history:
                            db_item = {
                                'stock_id': stock.id,
                                'date': parse_jalali_date(item.get('DEven', '')),
                                'j_date': item.get('DEven', ''),
                                'open_price': item.get('PriceFirst', None),
                                'high_price': item.get('PriceMax', None),
                                'low_price': item.get('PriceMin', None),
                                'close_price': item.get('PClosing', None),
                                'volume': item.get('QTotTran5J', None),
                                'value': item.get('QTotCap', None),
                                'count': item.get('ZTotTran', None)
                            }
                            db_history.append(db_item)
                        
                        if db_history:
                            updated = self.db.add_price_history(db_history)
                            total_updated += updated
                            logger.debug(f"Updated {updated} price records for {stock.ticker}")
                
                except Exception as e:
                    logger.error(f"Error updating price history for {stock.ticker}: {e}")
            
            duration = time.time() - start_time
            log_performance("update_price_history", duration, total_updated)
            logger.info(f"Updated {total_updated} price history records")
            return total_updated
            
        except Exception as e:
            logger.error(f"Error updating price history: {e}")
            return 0
    
    def update_ri_history(self, days: int = 30) -> int:
        """به‌روزرسانی تاریخچه حقیقی-حقوقی"""
        logger.info(f"Starting RI history update for last {days} days")
        start_time = time.time()
        
        try:
            from_date, to_date = self.api.get_date_range(days)
            
            # دریافت لیست سهام
            session = self.db.get_session()
            stocks = session.query(self.db.Stock).all()
            session.close()
            
            total_updated = 0
            for stock in stocks:
                try:
                    # بررسی آخرین تاریخ RI
                    last_date = self.db.get_last_ri_date(stock.id)
                    
                    if last_date:
                        last_dt = parse_jalali_date(last_date)
                        if last_dt:
                            from_dt = last_dt + timedelta(days=1)
                            from_date = format_jalali_date(from_dt)
                    
                    # دریافت تاریخچه RI
                    history = self.api.get_ri_history(stock.web_id, from_date, to_date)
                    if history:
                        # تبدیل به فرمت دیتابیس
                        db_history = []
                        for item in history:
                            db_item = {
                                'stock_id': stock.id,
                                'date': parse_jalali_date(item.get('DEven', '')),
                                'j_date': item.get('DEven', ''),
                                'individual_buy_volume': item.get('QTotTran5Buy_N', None),
                                'individual_sell_volume': item.get('QTotTran5Sell_N', None),
                                'individual_buy_value': item.get('QTotCapBuy_N', None),
                                'individual_sell_value': item.get('QTotCapSell_N', None),
                                'institutional_buy_volume': item.get('QTotTran5Buy_I', None),
                                'institutional_sell_volume': item.get('QTotTran5Sell_I', None),
                                'institutional_buy_value': item.get('QTotCapBuy_I', None),
                                'institutional_sell_value': item.get('QTotCapSell_I', None)
                            }
                            db_history.append(db_item)
                        
                        if db_history:
                            updated = self.db.add_ri_history(db_history)
                            total_updated += updated
                            logger.debug(f"Updated {updated} RI records for {stock.ticker}")
                
                except Exception as e:
                    logger.error(f"Error updating RI history for {stock.ticker}: {e}")
            
            duration = time.time() - start_time
            log_performance("update_ri_history", duration, total_updated)
            logger.info(f"Updated {total_updated} RI history records")
            return total_updated
            
        except Exception as e:
            logger.error(f"Error updating RI history: {e}")
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

def main():
    parser = argparse.ArgumentParser(description='TSE Data Collector')
    parser.add_argument('--mode', choices=['full', 'continuous', 'stocks', 'sectors', 'indices', 'prices', 'ri'], 
                       default='full', help='Update mode')
    parser.add_argument('--days', type=int, default=30, help='Number of days to update')
    parser.add_argument('--interval', type=int, default=None, help='Update interval in seconds')
    
    args = parser.parse_args()
    
    collector = TSEDataCollector()
    
    try:
        if args.mode == 'full':
            results = collector.run_full_update()
            print(f"Update completed: {results}")
            
        elif args.mode == 'continuous':
            collector.run_continuous_update(args.interval)
            
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
            
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
