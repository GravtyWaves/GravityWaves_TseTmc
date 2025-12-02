def get_postgres_session():
    """تابع کمکی برای بازگرداندن یک session دیتابیس PostgreSQL"""
    db = PostgreSQLDatabase()
    return db.get_session()
"""
PostgreSQL database implementation for TSE data collector
"""

from typing import List, Dict, Any, Optional
from sqlalchemy import and_
from sqlalchemy.orm import Session

from .base import DatabaseBase
from .models import (
    Stock, PriceHistory, RIHistory, Index, IndexHistory, Sector, 
    SectorIndexHistory, Shareholder, MajorShareholderHistory, IntradayTrade, USDHistory
)
import logging

logger = logging.getLogger(__name__)

class PostgreSQLDatabase(DatabaseBase):
    """PostgreSQL implementation of DatabaseBase"""

    # Expose models as attributes for testing
    Stock = Stock
    PriceHistory = PriceHistory
    RIHistory = RIHistory
    Index = Index
    IndexHistory = IndexHistory
    Sector = Sector
    SectorIndexHistory = SectorIndexHistory
    Shareholder = Shareholder
    MajorShareholderHistory = MajorShareholderHistory
    IntradayTrade = IntradayTrade
    USDHistory = USDHistory

    def add_stock(self, stock_data: Dict[str, Any]) -> Optional[Stock]:
        session = self.get_session()
        try:
            # بررسی وجود سهام
            existing = session.query(Stock).filter(
                Stock.ticker == stock_data['ticker']
            ).first()

            if existing:
                logger.debug(f"Stock {stock_data['ticker']} already exists")
                return None

            stock = Stock(**stock_data)
            session.add(stock)
            session.commit()
            # Ensure all attributes are loaded before expunging
            session.refresh(stock)
            session.expunge(stock)
            logger.info(f"Added new stock: {stock_data['ticker']}")
            return stock

        except Exception as e:
            session.rollback()
            logger.error(f"Error adding stock {stock_data['ticker']}: {e}")
            return None
        finally:
            session.close()
    
    def get_stock_by_ticker(self, ticker: str) -> Optional[Stock]:
        session = self.get_session()
        try:
            return session.query(Stock).filter(Stock.ticker == ticker).first()
        finally:
            session.close()
    
    def get_stock_by_web_id(self, web_id: str) -> Optional[Stock]:
        session = self.get_session()
        try:
            return session.query(Stock).filter(Stock.web_id == web_id).first()
        finally:
            session.close()
    
    def get_sector_by_code(self, sector_code: float) -> Optional[Sector]:
        session = self.get_session()
        try:
            return session.query(Sector).filter(Sector.sector_code == sector_code).first()
        finally:
            session.close()
    
    def add_price_history(self, history_data: List[Dict[str, Any]]) -> int:
        return self.batch_insert(PriceHistory, history_data)
    
    def add_ri_history(self, history_data: List[Dict[str, Any]]) -> int:
        return self.batch_insert(RIHistory, history_data)
    
    def add_index(self, index_data: Dict[str, Any]) -> Optional[Index]:
        session = self.get_session()
        try:
            # بررسی وجود شاخص
            existing = session.query(Index).filter(
                Index.name == index_data['name']
            ).first()

            if existing:
                logger.debug(f"Index {index_data['name']} already exists")
                # Ensure all attributes are loaded before expunging
                session.refresh(existing)
                session.expunge(existing)
                return existing

            index = Index(**index_data)
            session.add(index)
            session.commit()
            # Ensure all attributes are loaded before expunging
            session.refresh(index)
            session.expunge(index)
            logger.info(f"Added new index: {index_data['name']}")
            return index

        except Exception as e:
            session.rollback()
            logger.error(f"Error adding index {index_data['name']}: {e}")
            return None
        finally:
            session.close()
    
    def add_index_history(self, history_data: List[Dict[str, Any]]) -> int:
        return self.batch_insert(IndexHistory, history_data)
    
    def add_sector_index_history(self, history_data: List[Dict[str, Any]]) -> int:
        return self.batch_insert(SectorIndexHistory, history_data)
    
    def add_shareholder(self, shareholder_data: Dict[str, Any]) -> Optional[Shareholder]:
        session = self.get_session()
        try:
            # بررسی وجود سهامدار
            existing = session.query(Shareholder).filter(
                Shareholder.shareholder_id == shareholder_data['shareholder_id']
            ).first()

            if existing:
                logger.debug(f"Shareholder {shareholder_data['shareholder_id']} already exists")
                # Ensure all attributes are loaded before expunging
                session.refresh(existing)
                session.expunge(existing)
                return existing

            shareholder = Shareholder(**shareholder_data)
            session.add(shareholder)
            session.commit()
            # Ensure all attributes are loaded before expunging
            session.refresh(shareholder)
            session.expunge(shareholder)
            logger.info(f"Added new shareholder: {shareholder_data['name']}")
            return shareholder

        except Exception as e:
            session.rollback()
            logger.error(f"Error adding shareholder {shareholder_data['name']}: {e}")
            return None
        finally:
            session.close()
    
    def get_shareholder_by_id(self, shareholder_id: str) -> Optional[Shareholder]:
        session = self.get_session()
        try:
            return session.query(Shareholder).filter(Shareholder.shareholder_id == shareholder_id).first()
        finally:
            session.close()
    
    def add_major_shareholder_history(self, history_data: List[Dict[str, Any]]) -> int:
        return self.batch_insert(MajorShareholderHistory, history_data)
    
    def add_intraday_trades(self, trades_data: List[Dict[str, Any]]) -> int:
        return self.batch_insert(IntradayTrade, trades_data)
    
    def add_usd_history(self, history_data: List[Dict[str, Any]]) -> int:
        return self.batch_insert(USDHistory, history_data)
    
    def get_last_price_date(self, stock_id: int) -> Optional[str]:
        session = self.get_session()
        try:
            result = session.query(PriceHistory.j_date).filter(
                PriceHistory.stock_id == stock_id
            ).order_by(PriceHistory.date.desc()).first()
            
            return result[0] if result else None
        finally:
            session.close()
    
    def get_last_ri_date(self, stock_id: int) -> Optional[str]:
        session = self.get_session()
        try:
            result = session.query(RIHistory.j_date).filter(
                RIHistory.stock_id == stock_id
            ).order_by(RIHistory.date.desc()).first()
            
            return result[0] if result else None
        finally:
            session.close()
    
    def get_last_index_date(self, index_id: int) -> Optional[str]:
        session = self.get_session()
        try:
            result = session.query(IndexHistory.j_date).filter(
                IndexHistory.index_id == index_id
            ).order_by(IndexHistory.date.desc()).first()
            
            return result[0] if result else None
        finally:
            session.close()
    
    def get_last_sector_index_date(self, sector_id: int) -> Optional[str]:
        session = self.get_session()
        try:
            result = session.query(SectorIndexHistory.j_date).filter(
                SectorIndexHistory.sector_id == sector_id
            ).order_by(SectorIndexHistory.date.desc()).first()
            
            return result[0] if result else None
        finally:
            session.close()
    
    def get_last_shareholder_date(self, stock_id: int) -> Optional[str]:
        session = self.get_session()
        try:
            result = session.query(MajorShareholderHistory.j_date).filter(
                MajorShareholderHistory.stock_id == stock_id
            ).order_by(MajorShareholderHistory.date.desc()).first()
            
            return result[0] if result else None
        finally:
            session.close()
    
    def get_last_usd_date(self) -> Optional[str]:
        session = self.get_session()
        try:
            result = session.query(USDHistory.j_date).order_by(USDHistory.date.desc()).first()
            return result[0] if result else None
        finally:
            session.close()