from sqlalchemy import Column, Integer, String, Date, Numeric, BigInteger, Boolean, ForeignKey, UniqueConstraint, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Sector(Base):
    __tablename__ = 'sectors'
    
    id = Column(Integer, primary_key=True)
    sector_code = Column(Float, unique=True, nullable=False)  # کد صنعت
    sector_name = Column(String(200), nullable=False)  # نام صنعت به فارسی
    sector_name_en = Column(String(200))  # نام صنعت به انگلیسی
    naics_code = Column(String(50))  # کد NAICS
    naics_name = Column(String(200))  # نام NAICS
    
    # ارتباط با جدول سهام
    stocks = relationship("Stock", back_populates="sector")
    
    __table_args__ = (
        UniqueConstraint('sector_code', name='uq_sector_code'),
    )

class Stock(Base):
    __tablename__ = 'stocks'
    
    id = Column(Integer, primary_key=True)
    ticker = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    web_id = Column(String(50), unique=True, nullable=False)
    market = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    sector_id = Column(Integer, ForeignKey('sectors.id'), nullable=True)  # ارتباط با صنعت
    
    # ارتباط با جداول دیگر
    sector = relationship("Sector", back_populates="stocks")
    price_history = relationship("PriceHistory", back_populates="stock")
    ri_history = relationship("RIHistory", back_populates="stock")
    intraday_trades = relationship("IntradayTrade", back_populates="stock")
    shareholder_history = relationship("MajorShareholderHistory", back_populates="stock")
    
    __table_args__ = (
        UniqueConstraint('ticker', name='uq_ticker'),
        UniqueConstraint('web_id', name='uq_web_id'),
    )

class PriceHistory(Base):
    __tablename__ = 'price_history'
    
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    j_date = Column(String(10), nullable=False)  # تاریخ شمسی YYYY-MM-DD
    date = Column(Date, nullable=False)  # تاریخ میلادی
    weekday = Column(String(10))
    open_price = Column(BigInteger)
    high_price = Column(BigInteger)
    low_price = Column(BigInteger)
    close_price = Column(BigInteger)
    final_price = Column(BigInteger)
    volume = Column(BigInteger)
    value = Column(BigInteger)
    num_trades = Column(Integer)
    adjusted_open = Column(BigInteger)
    adjusted_high = Column(BigInteger)
    adjusted_low = Column(BigInteger)
    adjusted_close = Column(BigInteger)
    adjusted_final = Column(BigInteger)
    volume_adj = Column(BigInteger)  # حجم تعدیل شده: (final_adj * volume) / final
    
    # ارتباط با جدول سهام
    stock = relationship("Stock", back_populates="price_history")
    
    __table_args__ = (
        UniqueConstraint('stock_id', 'j_date', name='uq_stock_date'),
    )

class RIHistory(Base):
    __tablename__ = 'ri_history'
    
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    j_date = Column(String(10), nullable=False)  # تاریخ شمسی YYYY-MM-DD
    date = Column(Date, nullable=False)  # تاریخ میلادی
    weekday = Column(String(10))
    no_buy_r = Column(Integer)  # تعداد خرید حقیقی
    no_buy_i = Column(Integer)  # تعداد خرید حقوقی
    no_sell_r = Column(Integer)  # تعداد فروش حقیقی
    no_sell_i = Column(Integer)  # تعداد فروش حقوقی
    vol_buy_r = Column(BigInteger)  # حجم خرید حقیقی
    vol_buy_i = Column(BigInteger)  # حجم خرید حقوقی
    vol_sell_r = Column(BigInteger)  # حجم فروش حقیقی
    vol_sell_i = Column(BigInteger)  # حجم فروش حقوقی
    val_buy_r = Column(BigInteger)  # ارزش خرید حقیقی
    val_buy_i = Column(BigInteger)  # ارزش خرید حقوقی
    val_sell_r = Column(BigInteger)  # ارزش فروش حقیقی
    val_sell_i = Column(BigInteger)  # ارزش فروش حقوقی
    
    # ارتباط با جدول سهام
    stock = relationship("Stock", back_populates="ri_history")
    
    __table_args__ = (
        UniqueConstraint('stock_id', 'j_date', name='uq_ri_stock_date'),
    )

class Index(Base):
    __tablename__ = 'indices'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    web_id = Column(String(50), unique=True, nullable=False)
    
    # ارتباط با جدول تاریخچه شاخص
    history = relationship("IndexHistory", back_populates="index")
    
    __table_args__ = (
        UniqueConstraint('name', name='uq_index_name'),
        UniqueConstraint('web_id', name='uq_index_web_id'),
    )

class IndexHistory(Base):
    __tablename__ = 'index_history'
    
    id = Column(Integer, primary_key=True)
    index_id = Column(Integer, ForeignKey('indices.id'), nullable=False)
    j_date = Column(String(10), nullable=False)  # تاریخ شمسی YYYY-MM-DD
    date = Column(Date, nullable=False)  # تاریخ میلادی
    weekday = Column(String(10))
    open_price = Column(Numeric(15, 2))
    high_price = Column(Numeric(15, 2))
    low_price = Column(Numeric(15, 2))
    close_price = Column(Numeric(15, 2))
    adj_close = Column(Numeric(15, 2))
    volume = Column(BigInteger)
    
    # ارتباط با جدول شاخص
    index = relationship("Index", back_populates="history")
    
    __table_args__ = (
        UniqueConstraint('index_id', 'j_date', name='uq_index_date'),
    )

class SectorIndexHistory(Base):
    __tablename__ = 'sector_index_history'
    
    id = Column(Integer, primary_key=True)
    sector_id = Column(Integer, ForeignKey('sectors.id'), nullable=False)
    j_date = Column(String(10), nullable=False)  # تاریخ شمسی YYYY-MM-DD
    date = Column(Date, nullable=False)  # تاریخ میلادی
    weekday = Column(String(10))
    open_price = Column(Numeric(15, 2))
    high_price = Column(Numeric(15, 2))
    low_price = Column(Numeric(15, 2))
    close_price = Column(Numeric(15, 2))
    adj_close = Column(Numeric(15, 2))
    volume = Column(BigInteger)
    
    # ارتباط با جدول صنایع
    sector = relationship("Sector")
    
    __table_args__ = (
        UniqueConstraint('sector_id', 'j_date', name='uq_sector_index_date'),
    )

class Shareholder(Base):
    __tablename__ = 'shareholders'
    
    id = Column(Integer, primary_key=True)
    shareholder_id = Column(String(50), unique=True, nullable=False)  # شناسه سهامدار در TSE
    name = Column(String(200), nullable=False)  # نام سهامدار
    is_individual = Column(Boolean, default=True)  # آیا شخص حقیقی است؟
    
    # ارتباط با جدول تاریخچه سهامداری
    history = relationship("MajorShareholderHistory", back_populates="shareholder")
    
    __table_args__ = (
        UniqueConstraint('shareholder_id', name='uq_shareholder_id'),
    )

class MajorShareholderHistory(Base):
    __tablename__ = 'major_shareholder_history'
    
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    shareholder_id = Column(Integer, ForeignKey('shareholders.id'), nullable=False)
    j_date = Column(String(10), nullable=False)  # تاریخ شمسی YYYY-MM-DD
    date = Column(Date, nullable=False)  # تاریخ میلادی
    shares_count = Column(BigInteger, nullable=False)  # تعداد سهام
    percentage = Column(Numeric(5, 2), nullable=False)  # درصد مالکیت
    
    # ارتباط با جداول دیگر
    stock = relationship("Stock")
    shareholder = relationship("Shareholder", back_populates="history")
    
    __table_args__ = (
        UniqueConstraint('stock_id', 'shareholder_id', 'j_date', name='uq_major_shareholder'),
    )

class IntradayTrade(Base):
    __tablename__ = 'intraday_trades'
    
    id = Column(Integer, primary_key=True)
    stock_id = Column(Integer, ForeignKey('stocks.id'), nullable=False)
    j_date = Column(String(10), nullable=False)  # تاریخ شمسی YYYY-MM-DD
    date = Column(Date, nullable=False)  # تاریخ میلادی
    time = Column(String(8), nullable=False)  # زمان معامله HH:MM:SS
    price = Column(BigInteger, nullable=False)  # قیمت معامله
    volume = Column(BigInteger, nullable=False)  # حجم معامله
    value = Column(BigInteger, nullable=False)  # ارزش معامله
    
    # ارتباط با جدول سهام
    stock = relationship("Stock")
    
    __table_args__ = (
        UniqueConstraint('stock_id', 'j_date', 'time', name='uq_intraday_trade'),
    )

class USDHistory(Base):
    __tablename__ = 'usd_history'
    
    id = Column(Integer, primary_key=True)
    j_date = Column(String(10), nullable=False)  # تاریخ شمسی YYYY-MM-DD
    date = Column(Date, nullable=False)  # تاریخ میلادی
    weekday = Column(String(10))
    open_price = Column(Numeric(15, 2))  # قیمت باز شدن
    high_price = Column(Numeric(15, 2))  # بیشترین قیمت
    low_price = Column(Numeric(15, 2))  # کمترین قیمت
    close_price = Column(Numeric(15, 2))  # قیمت پایانی
    adj_close = Column(Numeric(15, 2))  # قیمت پایانی تعدیل شده
    volume = Column(BigInteger)  # حجم معاملات
    
    __table_args__ = (
        UniqueConstraint('j_date', name='uq_usd_date'),
    )
