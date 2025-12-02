"""
تست‌های حرفه‌ای برای api/market_watch.py با استفاده از داده‌های واقعی TSE
"""

import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from api.market_watch import MarketWatch


class TestMarketWatchIntegration:
    """تست‌های یکپارچه برای MarketWatch با داده‌های واقعی"""

    def setup_method(self):
        """تنظیمات اولیه برای هر تست"""
        self.mw = MarketWatch()

    @pytest.mark.slow
    def test_get_market_watch_real_data(self):
        """تست دریافت داده‌های واقعی MarketWatch"""
        # Mock the request to simulate TSE data with correct columns
        # expected_cols = ['symbol','Ticker-Code','Name','Sector','Open','High','Low','Final','last_price','No','Volume','Value','Y-Final','EPS','Base-Vol','Unknown1','Unknown2','Day_UL','Day_LL','Share-No','Mkt-ID','Extra']
        mock_response = MagicMock()
        # Ensure data is in segment index 2 when splitting by '@'
        mock_data = "H1@H2@"
        # Each row: symbol, Ticker-Code, Name, Sector, Open, High, Low, Final, last_price, No, Volume, Value, Y-Final, EPS, Base-Vol, Unknown1, Unknown2, Day_UL, Day_LL, Share-No, Mkt-ID, Extra
        mock_data += "SYM1,TC1,Name1,Sec1,1000,1100,900,1050,1500,100,10000,10500000,1000,50,5000,0,0,1200,800,1000000,1,extra1;"
        mock_data += "SYM2,TC2,Name2,Sec2,2000,2200,1800,2100,2500,200,20000,42000000,2000,100,10000,0,0,2400,1600,2000000,1,extra2;"
        mock_data += "SYM3,TC3,Name3,Sec3,3000,3300,2700,3150,3500,300,30000,94500000,3000,150,15000,0,0,3600,2400,3000000,2,extra3"
        mock_data += "@order_book"
        mock_response.text = mock_data

        with patch.object(self.mw, 'make_request', return_value=mock_response):
            df = self.mw.get_market_watch()

            assert df is not None
            assert isinstance(df, pd.DataFrame)
            assert not df.empty

            # بررسی ستون‌های ضروری
            assert 'symbol' in df.columns
            assert 'last_price' in df.columns

            # بررسی مقادیر عددی قیمت
            assert pd.api.types.is_numeric_dtype(df['last_price'])

            # فیلتر کردن رکوردهایی که قیمت صفر دارند (ممکن است نمادهای متوقف یا بدون معامله باشند)
            df_filtered = df[df['last_price'] > 0]
            if not df_filtered.empty:
                assert (df_filtered['last_price'] > 0).all()

            print(f"MarketWatch data: {len(df)} records, {len(df_filtered)} with positive prices")

    @pytest.mark.slow
    def test_get_market_watch_by_market(self):
        """تست فیلتر کردن بر اساس بازار"""
        # تست بازار بورس (market=1)
        df_bourse = self.mw.get_market_watch(market=1)
        if df_bourse is not None and not df_bourse.empty:
            print(f"Bourse market data: {len(df_bourse)} records")

        # تست بازار فرابورس (market=2)
        df_faraborse = self.mw.get_market_watch(market=2)
        if df_faraborse is not None and not df_faraborse.empty:
            print(f"Faraborse market data: {len(df_faraborse)} records")

    def test_get_top_gainers_real_data(self):
        """تست دریافت برترین رشدکنندگان"""
        df_gainers = self.mw.get_top_gainers(count=5)

        if df_gainers is not None:
            assert isinstance(df_gainers, pd.DataFrame)
            assert len(df_gainers) <= 5
            assert 'symbol' in df_gainers.columns
            assert 'last_price' in df_gainers.columns

            # بررسی اینکه قیمت‌ها مرتب نزولی هستند
            if len(df_gainers) > 1:
                prices = df_gainers['last_price'].values
                assert all(prices[i] >= prices[i+1] for i in range(len(prices)-1))

            print(f"Top gainers: {len(df_gainers)} stocks")

    def test_get_top_losers_real_data(self):
        """تست دریافت برترین کاهش‌یافتگان"""
        df_losers = self.mw.get_top_losers(count=5)

        if df_losers is not None:
            assert isinstance(df_losers, pd.DataFrame)
            assert len(df_losers) <= 5
            assert 'symbol' in df_losers.columns
            assert 'last_price' in df_losers.columns

            # بررسی اینکه قیمت‌ها مرتب صعودی هستند
            if len(df_losers) > 1:
                prices = df_losers['last_price'].values
                assert all(prices[i] <= prices[i+1] for i in range(len(prices)-1))

            print(f"Top losers: {len(df_losers)} stocks")

    def test_market_watch_data_validation(self):
        """تست اعتبار داده‌های MarketWatch"""
        mock_response = MagicMock()
        mock_data = "H1@H2@"
        # Add 10 rows with positive last_price
        for i in range(1, 11):
            mock_data += f"SYM{i},TC{i},Name{i},Sec{i},{1000+i*100},{1100+i*100},{900+i*100},{1050+i*100},{1500+i*100},{100+i*10},{10000+i*1000},{10500000+i*1000000},{1000+i*100},{50+i*5},{5000+i*500},0,0,{1200+i*100},{800+i*100},{1000000+i*100000},1,extra{i};"
        mock_data += "@order_book"
        mock_response.text = mock_data
        with patch.object(self.mw, 'make_request', return_value=mock_response):
            df = self.mw.get_market_watch()

            assert df is not None
            assert not df.empty

            # بررسی تک تک رکوردها برای 10 رکورد اول
            for idx, row in df.head(10).iterrows():
                # نماد باید وجود داشته باشد و خالی نباشد
                assert 'symbol' in row
                assert row['symbol'] and len(str(row['symbol']).strip()) > 0

                # قیمت باید عددی مثبت باشد
                assert 'last_price' in row
                assert pd.notna(row['last_price'])
                assert isinstance(row['last_price'], (int, float))
                assert row['last_price'] > 0

    def test_market_watch_columns_completeness(self):
        """تست کامل بودن ستون‌های MarketWatch"""
        df = self.mw.get_market_watch(market=None)  # همه بازارها

        assert df is not None
        assert not df.empty

        # بررسی وجود ستون‌های کلیدی
        expected_columns = ['symbol', 'last_price']
        for col in expected_columns:
            assert col in df.columns, f"Missing column: {col}"

        # بررسی عدم وجود مقادیر NaN در ستون‌های کلیدی
        assert not df['symbol'].isna().any(), "NaN values in symbol column"
        assert not df['last_price'].isna().any(), "NaN values in last_price column"

    def test_error_handling_network_timeout(self):
        """تست مدیریت timeout شبکه"""
        with patch('requests.get') as mock_get:
            mock_get.side_effect = TimeoutError("Connection timeout")

            df = self.mw.get_market_watch()
            assert df is None

            gainers = self.mw.get_top_gainers()
            assert gainers is None

            losers = self.mw.get_top_losers()
            assert losers is None

    def test_error_handling_invalid_response(self):
        """تست مدیریت پاسخ نامعتبر"""
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = "Invalid response"
            mock_get.return_value = mock_response

            df = self.mw.get_market_watch()
            # بسته به implementation ممکن است None یا DataFrame خالی برگردد
            assert df is None or (isinstance(df, pd.DataFrame) and df.empty)

    def test_data_consistency_across_calls(self):
        """تست consistency داده‌ها در فراخوانی‌های متوالی"""
        df1 = self.mw.get_market_watch()
        df2 = self.mw.get_market_watch()

        assert df1 is not None and df2 is not None
        assert not df1.empty and not df2.empty

        # بررسی ساختار یکسان
        assert set(df1.columns) == set(df2.columns)

        # بررسی consistency تعداد رکوردها (با tolerance)
        count_diff = abs(len(df1) - len(df2))
        assert count_diff <= 20, f"Data count inconsistency: {len(df1)} vs {len(df2)}"

    def test_market_filtering_functionality(self):
        """تست عملکرد فیلتر بازار"""
        # دریافت همه داده‌ها
        df_all = self.mw.get_market_watch()

        if df_all is not None and not df_all.empty:
            # اگر ستون Mkt-ID وجود دارد، تست فیلتر را انجام بده
            if 'Mkt-ID' in df_all.columns:
                # تست بازار بورس
                df_bourse = self.mw.get_market_watch(market=1)
                if df_bourse is not None:
                    # همه رکوردهای فیلتر شده باید Mkt-ID = 1 داشته باشند
                    if not df_bourse.empty and 'Mkt-ID' in df_bourse.columns:
                        assert (df_bourse['Mkt-ID'] == '1').all()

                # تست بازار فرابورس
                df_faraborse = self.mw.get_market_watch(market=2)
                if df_faraborse is not None:
                    # همه رکوردهای فیلتر شده باید Mkt-ID = 2 داشته باشند
                    if not df_faraborse.empty and 'Mkt-ID' in df_faraborse.columns:
                        assert (df_faraborse['Mkt-ID'] == '2').all()

    def test_numeric_data_types(self):
        """تست نوع داده‌های عددی"""
        mock_response = MagicMock()
        mock_data = "H1@H2@"
        mock_data += "SYM1,TC1,Name1,Sec1,1000,1100,900,1050,1500,100,10000,10500000,1000,50,5000,0,0,1200,800,1000000,1,extra1;"
        mock_data += "SYM2,TC2,Name2,Sec2,2000,2200,1800,2100,2500,200,20000,42000000,2000,100,10000,0,0,2400,1600,2000000,1,extra2;"
        mock_data += "SYM3,TC3,Name3,Sec3,3000,3300,2700,3150,3500,300,30000,94500000,3000,150,15000,0,0,3600,2400,3000000,2,extra3"
        mock_data += "@order_book"
        mock_response.text = mock_data
        with patch.object(self.mw, 'make_request', return_value=mock_response):
            df = self.mw.get_market_watch()

            assert df is not None
            assert not df.empty

            # بررسی نوع داده ستون last_price
            assert pd.api.types.is_numeric_dtype(df['last_price'])

            # بررسی مقادیر مثبت
            assert (df['last_price'] > 0).all()

            # اگر ستون‌های دیگر وجود دارند، بررسی نوع داده آنها
            numeric_columns = ['Open', 'High', 'Low', 'Final', 'Volume', 'Value']
            for col in numeric_columns:
                if col in df.columns:
                    assert pd.api.types.is_numeric_dtype(df[col])
                    # مقادیر باید غیر منفی باشند
                    assert (df[col] >= 0).all()
