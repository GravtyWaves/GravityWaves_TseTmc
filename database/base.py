from abc import ABC, abstractmethod
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import IntegrityError
from typing import List, Dict, Any, Optional
import logging
import json

from .models import (
    Base, Stock, PriceHistory, RIHistory, Index, IndexHistory, Sector, 
    SectorIndexHistory, Shareholder, MajorShareholderHistory, IntradayTrade, USDHistory
)
from config import DATABASE_URL, BATCH_SIZE, SECTORS_DATA_FILE

logger = logging.getLogger(__name__)

class DatabaseBase(ABC):
    def __init__(self):
        self.engine = create_engine(DATABASE_URL)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        self.create_tables()
    
    def create_tables(self):
        """ایجاد جداول در دیتابیس"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")
    
    def get_session(self) -> Session:
        """دریافت سشن دیتابیس"""
        return self.SessionLocal()
    
    def load_sectors_from_file(self):
        """بارگذاری داده‌های صنایع از فایل"""
        try:
            with open(SECTORS_DATA_FILE, 'r', encoding='utf-8') as f:
                sectors_data = json.load(f)
            
            session = self.get_session()
            try:
                for sector_data in sectors_data:
                    # بررسی وجود صنعت
                    existing = session.query(Sector).filter(
                        Sector.sector_code == sector_data['SectorCode']
                    ).first()
                    
                    if not existing:
                        sector = Sector(
                            sector_code=sector_data['SectorCode'],
                            sector_name=sector_data['SectorName'],
                            sector_name_en=sector_data['SectorNameEn'],
                            naics_code=sector_data['NAICSCode'],
                            naics_name=sector_data['NAICSName']
                        )
                        session.add(sector)
                
                session.commit()
                logger.info(f"Loaded {len(sectors_data)} sectors from file")
            except Exception as e:
                session.rollback()
                logger.error(f"Error loading sectors: {e}")
            finally:
                session.close()
        except Exception as e:
            logger.error(f"Error reading sectors file: {e}")
    
    @abstractmethod
    def add_stock(self, stock_data: Dict[str, Any]) -> Optional[Stock]:
        """افزودن سهام جدید به دیتابیس"""
        pass
    
    @abstractmethod
    def get_stock_by_ticker(self, ticker: str) -> Optional[Stock]:
        """دریافت اطلاعات سهام با تیکر"""
        pass
    
    @abstractmethod
    def get_stock_by_web_id(self, web_id: str) -> Optional[Stock]:
        """دریافت اطلاعات سهام با وب‌آیدی"""
        pass
    
    @abstractmethod
    def get_sector_by_code(self, sector_code: float) -> Optional[Sector]:
        """دریافت اطلاعات صنعت با کد صنعت"""
        pass
    
    @abstractmethod
    def add_price_history(self, history_data: List[Dict[str, Any]]) -> int:
        """افزودن تاریخچه قیمت سهام"""
        pass
    
    @abstractmethod
    def add_ri_history(self, history_data: List[Dict[str, Any]]) -> int:
        """افزودن تاریخچه حقیقی-حقوقی"""
        pass
    
    @abstractmethod
    def add_index(self, index_data: Dict[str, Any]) -> Optional[Index]:
        """افزودن شاخص جدید"""
        pass
    
    @abstractmethod
    def add_index_history(self, history_data: List[Dict[str, Any]]) -> int:
        """افزودن تاریخچه شاخص"""
        pass
    
    @abstractmethod
    def add_sector_index_history(self, history_data: List[Dict[str, Any]]) -> int:
        """افزودن تاریخچه شاخص صنایع"""
        pass
    
    @abstractmethod
    def add_shareholder(self, shareholder_data: Dict[str, Any]) -> Optional[Shareholder]:
        """افزودن سهامدار جدید"""
        pass
    
    @abstractmethod
    def get_shareholder_by_id(self, shareholder_id: str) -> Optional[Shareholder]:
        """دریافت اطلاعات سهامدار با شناسه"""
        pass
    
    @abstractmethod
    def add_major_shareholder_history(self, history_data: List[Dict[str, Any]]) -> int:
        """افزودن تاریخچه سهامداری عمده"""
        pass
    
    @abstractmethod
    def add_intraday_trades(self, trades_data: List[Dict[str, Any]]) -> int:
        """افزودن معاملات داخل روزی"""
        pass
    
    @abstractmethod
    def add_usd_history(self, history_data: List[Dict[str, Any]]) -> int:
        """افزودن تاریخچه قیمت دلار"""
        pass
    
    @abstractmethod
    def get_last_price_date(self, stock_id: int) -> Optional[str]:
        """دریافت آخرین تاریخ قیمت برای یک سهم"""
        pass
    
    @abstractmethod
    def get_last_ri_date(self, stock_id: int) -> Optional[str]:
        """دریافت آخرین تاریخ حقیقی-حقوقی برای یک سهم"""
        pass
    
    @abstractmethod
    def get_last_index_date(self, index_id: int) -> Optional[str]:
        """دریافت آخرین تاریخ برای یک شاخص"""
        pass
    
    @abstractmethod
    def get_last_sector_index_date(self, sector_id: int) -> Optional[str]:
        """دریافت آخرین تاریخ شاخص برای یک صنعت"""
        pass
    
    @abstractmethod
    def get_last_shareholder_date(self, stock_id: int) -> Optional[str]:
        """دریافت آخرین تاریخ سهامداری برای یک سهم"""
        pass
    
    @abstractmethod
    def get_last_usd_date(self) -> Optional[str]:
        """دریافت آخرین تاریخ قیمت دلار"""
        pass
    
    def batch_insert(self, model_class, data_list: List[Dict[str, Any]]) -> int:
        """درج دسته‌ای داده‌ها"""
        if not data_list:
            return 0
            
        inserted_count = 0
        session = self.get_session()
        
        try:
            for i in range(0, len(data_list), BATCH_SIZE):
                batch = data_list[i:i+BATCH_SIZE]
                objects = [model_class(**item) for item in batch]
                session.bulk_save_objects(objects)
                session.commit()
                inserted_count += len(batch)
                logger.debug(f"Inserted {inserted_count} records into {model_class.__tablename__}")
                
        except IntegrityError as e:
            session.rollback()
            logger.error(f"Integrity error during batch insert: {e}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error during batch insert: {e}")
        finally:
            session.close()
            
        return inserted_count
