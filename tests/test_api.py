
import pytest
import json
import requests
from datetime import datetime
from unittest.mock import patch, MagicMock, mock_open
from api.tse_api import TSEAPIClient


class TestTSEAPIClient:
    @pytest.fixture
    def api_client(self):
        return TSEAPIClient()

    def test_init(self, api_client):
        assert api_client.base_url == "http://www.tsetmc.com/tsev2/data"

    def test_get_instrument_search_success(self, api_client):
        with patch.object(api_client, '_make_request', return_value='instrument1,123456,Stock1\ninstrument2,789012,Stock2') as mock_make_request:
            result = api_client.get_instrument_search('test')

            assert result == 'instrument1,123456,Stock1\ninstrument2,789012,Stock2'
            mock_make_request.assert_called_once_with("InstrumentSearch", {'search': 'test'})

    def test_get_instrument_search_failure(self, api_client):
        with patch.object(api_client, '_make_request', return_value=None) as mock_make_request:
            result = api_client.get_instrument_search('test')

            assert result is None
            mock_make_request.assert_called_once_with("InstrumentSearch", {'search': 'test'})

    def test_get_instrument_info_success(self, api_client):
        with patch.object(api_client, '_make_request', return_value='123456;Stock1;بازار اول;ABC;123456') as mock_make_request:
            result = api_client.get_instrument_info('123456')

            assert result == '123456;Stock1;بازار اول;ABC;123456'
            mock_make_request.assert_called_once_with("InstrumentInfo", {'webId': '123456'})

    def test_get_instrument_info_failure(self, api_client):
        with patch.object(api_client, '_make_request', return_value=None) as mock_make_request:
            result = api_client.get_instrument_info('123456')

            assert result is None
            mock_make_request.assert_called_once_with("InstrumentInfo", {'webId': '123456'})

    def test_get_price_history_success(self, api_client):
        with patch.object(api_client, '_make_request', return_value='2023/01/01,1000,1100,900,1050,1000000,1000000000,1000') as mock_make_request:
            result = api_client.get_price_history('123456', '2023/01/01', '2023/01/31')

            assert result == '2023/01/01,1000,1100,900,1050,1000000,1000000000,1000'
            mock_make_request.assert_called_once_with("PriceHistory", {'webId': '123456', 'fromDate': '2023/01/01', 'toDate': '2023/01/31'})

    def test_get_price_history_failure(self, api_client):
        with patch.object(api_client, '_make_request', return_value=None) as mock_make_request:
            result = api_client.get_price_history('123456', '2023/01/01', '2023/01/31')

            assert result is None
            mock_make_request.assert_called_once_with("PriceHistory", {'webId': '123456', 'fromDate': '2023/01/01', 'toDate': '2023/01/31'})

    def test_get_client_type_history_success(self, api_client):
        with patch.object(api_client, '_make_request', return_value='2023/01/01,500000,300000,500000000,300000000,500000,700000,500000000,700000000') as mock_make_request:
            result = api_client.get_client_type_history('123456', '2023/01/01', '2023/01/31')

            assert result == '2023/01/01,500000,300000,500000000,300000000,500000,700000,500000000,700000000'
            mock_make_request.assert_called_once_with("ClientTypeHistory", {'webId': '123456', 'fromDate': '2023/01/01', 'toDate': '2023/01/31'})

    def test_get_client_type_history_failure(self, api_client):
        with patch.object(api_client, '_make_request', return_value=None) as mock_make_request:
            result = api_client.get_client_type_history('123456', '2023/01/01', '2023/01/31')

            assert result is None
            mock_make_request.assert_called_once_with("ClientTypeHistory", {'webId': '123456', 'fromDate': '2023/01/01', 'toDate': '2023/01/31'})

    def test_get_index_history_success(self, api_client):
        with patch.object(api_client, '_make_request', return_value='2023/01/01,1000000,1000,0.1') as mock_make_request:
            result = api_client.get_index_history('123456', '2023/01/01', '2023/01/31')

            assert result == '2023/01/01,1000000,1000,0.1'
            mock_make_request.assert_called_once_with("IndexHistory", {'indexId': '123456', 'fromDate': '2023/01/01', 'toDate': '2023/01/31'})

    def test_get_index_history_failure(self, api_client):
        with patch.object(api_client, '_make_request', return_value=None) as mock_make_request:
            result = api_client.get_index_history('123456', '2023/01/01', '2023/01/31')

            assert result is None
            mock_make_request.assert_called_once_with("IndexHistory", {'indexId': '123456', 'fromDate': '2023/01/01', 'toDate': '2023/01/31'})

    def test_get_shareholder_history_success(self, api_client):
        with patch.object(api_client, '_make_request', return_value='123456789,سهامدار نمونه,1000000,10.5') as mock_make_request:
            result = api_client.get_shareholder_history('123456', '2023/01/01')

            assert result == '123456789,سهامدار نمونه,1000000,10.5'
            mock_make_request.assert_called_once_with("ShareholderHistory", {'webId': '123456', 'date': '2023/01/01'})

    def test_get_shareholder_history_failure(self, api_client):
        with patch.object(api_client, '_make_request', return_value=None) as mock_make_request:
            result = api_client.get_shareholder_history('123456', '2023/01/01')

            assert result is None
            mock_make_request.assert_called_once_with("ShareholderHistory", {'webId': '123456', 'date': '2023/01/01'})

    def test_get_intraday_trades_success(self, api_client):
        with patch.object(api_client, '_make_request', return_value='09:00:00,1000,10000,10000000') as mock_make_request:
            result = api_client.get_intraday_trades('123456', '2023/01/01')

            assert result == '09:00:00,1000,10000,10000000'
            mock_make_request.assert_called_once_with("IntradayTrades", {'webId': '123456', 'date': '2023/01/01'})

    def test_get_intraday_trades_failure(self, api_client):
        with patch.object(api_client, '_make_request', return_value=None) as mock_make_request:
            result = api_client.get_intraday_trades('123456', '2023/01/01')

            assert result is None
            mock_make_request.assert_called_once_with("IntradayTrades", {'webId': '123456', 'date': '2023/01/01'})

    def test_get_usd_history_success(self, api_client):
        with patch.object(api_client, '_make_request', return_value='2023/01/01,50000,1000,2.0') as mock_make_request:
            result = api_client.get_usd_history('2023/01/01', '2023/01/31')

            assert result == '2023/01/01,50000,1000,2.0'
            mock_make_request.assert_called_once_with("USDHistory", {'fromDate': '2023/01/01', 'toDate': '2023/01/31'})

    def test_get_usd_history_failure(self, api_client):
        with patch.object(api_client, '_make_request', return_value=None) as mock_make_request:
            result = api_client.get_usd_history('2023/01/01', '2023/01/31')

            assert result is None
            mock_make_request.assert_called_once_with("USDHistory", {'fromDate': '2023/01/01', 'toDate': '2023/01/31'})

    def test_get_sector_index_history_success(self, api_client):
        with patch.object(api_client, '_make_request', return_value='2023/01/01,1000000,1000,0.1') as mock_make_request:
            result = api_client.get_sector_index_history('1', '2023/01/01', '2023/01/31')

            assert result == '2023/01/01,1000000,1000,0.1'
            mock_make_request.assert_called_once_with("SectorIndexHistory", {'sectorCode': '1', 'fromDate': '2023/01/01', 'toDate': '2023/01/31'})

    def test_get_sector_index_history_failure(self, api_client):
        with patch.object(api_client, '_make_request', return_value=None) as mock_make_request:
            result = api_client.get_sector_index_history('1', '2023/01/01', '2023/01/31')

            assert result is None
            mock_make_request.assert_called_once_with("SectorIndexHistory", {'sectorCode': '1', 'fromDate': '2023/01/01', 'toDate': '2023/01/31'})

    def test_parse_instrument_search_valid(self, api_client):
        data = "ABC,123456,شرکت نمونه\nDEF,789012,شرکت دیگر"
        result = api_client.parse_instrument_search(data)

        expected = [
            {'ticker': 'ABC', 'web_id': '123456', 'name': 'شرکت نمونه'},
            {'ticker': 'DEF', 'web_id': '789012', 'name': 'شرکت دیگر'}
        ]
        assert result == expected

    def test_parse_instrument_search_empty(self, api_client):
        result = api_client.parse_instrument_search("")
        assert result == []

    def test_parse_instrument_search_invalid(self, api_client):
        result = api_client.parse_instrument_search("invalid,data")
        assert result == []

    def test_parse_instrument_info_valid(self, api_client):
        data = "123456;شرکت نمونه;بازار اول;ABC;123456"
        result = api_client.parse_instrument_info(data)

        expected = {
            'web_id': '123456',
            'name': 'شرکت نمونه',
            'market': 'بازار اول',
            'ticker': 'ABC',
            'tse_id': '123456'
        }
        assert result == expected

    def test_parse_instrument_info_invalid(self, api_client):
        result = api_client.parse_instrument_info("invalid;data")
        assert result is None

    def test_parse_price_history_valid(self, api_client):
        data = "1402/01/01,1000,1100,900,1050,1000000,1000000000,1000"
        result = api_client.parse_price_history(data, '123456')

        assert len(result) == 1
        assert result[0]['stock_id'] == '123456'
        assert result[0]['j_date'] == '1402/01/01'
        assert result[0]['close_price'] == 1050

    def test_parse_price_history_empty(self, api_client):
        result = api_client.parse_price_history("", '123456')
        assert result == []

    def test_parse_price_history_invalid(self, api_client):
        result = api_client.parse_price_history("invalid,data", '123456')
        assert result == []

    def test_parse_client_type_history_valid(self, api_client):
        data = "1402/01/01,500000,300000,500000000,300000000,500000,700000,500000000,700000000"
        result = api_client.parse_client_type_history(data, '123456')

        assert len(result) == 1
        assert result[0]['stock_id'] == '123456'
        assert result[0]['j_date'] == '1402/01/01'
        assert result[0]['vol_buy_r'] == 500000

    def test_parse_client_type_history_empty(self, api_client):
        result = api_client.parse_client_type_history("", '123456')
        assert result == []

    def test_parse_client_type_history_invalid(self, api_client):
        result = api_client.parse_client_type_history("invalid,data", '123456')
        assert result == []

    def test_parse_index_history_valid(self, api_client):
        data = "1402/01/01,1000000,1000,0.1"
        result = api_client.parse_index_history(data, '123456')

        assert len(result) == 1
        assert result[0]['index_id'] == '123456'
        assert result[0]['j_date'] == '1402/01/01'
        assert result[0]['value'] == 1000000.0

    def test_parse_index_history_empty(self, api_client):
        result = api_client.parse_index_history("", '123456')
        assert result == []

    def test_parse_index_history_invalid(self, api_client):
        result = api_client.parse_index_history("invalid,data", '123456')
        assert result == []

    def test_parse_shareholder_history_valid(self, api_client):
        data = "123456789,سهامدار نمونه,1000000,10.5"
        result = api_client.parse_shareholder_history(data, '123456', '1402/01/01')

        assert len(result) == 1
        assert result[0]['stock_id'] == '123456'
        assert result[0]['shareholder_id'] == '123456789'
        assert result[0]['j_date'] == '1402/01/01'

    def test_parse_shareholder_history_empty(self, api_client):
        result = api_client.parse_shareholder_history("", '123456', '1402/01/01')
        assert result == []

    def test_parse_shareholder_history_invalid(self, api_client):
        result = api_client.parse_shareholder_history("invalid,data", '123456', '1402/01/01')
        assert result == []

    def test_parse_intraday_trades_valid(self, api_client):
        data = "09:00:00,1000,10000,10000000"
        result = api_client.parse_intraday_trades(data, '123456', '1402/01/01')

        assert len(result) == 1
        assert result[0]['stock_id'] == '123456'
        assert result[0]['j_date'] == '1402/01/01'
        assert result[0]['time'] == '09:00:00'

    def test_parse_intraday_trades_empty(self, api_client):
        result = api_client.parse_intraday_trades("", '123456', '1402/01/01')
        assert result == []

    def test_parse_intraday_trades_invalid(self, api_client):
        result = api_client.parse_intraday_trades("invalid,data", '123456', '1402/01/01')
        assert result == []

    def test_parse_usd_history_valid(self, api_client):
        data = "1402/01/01,50000,1000,2.0"
        result = api_client.parse_usd_history(data)

        assert len(result) == 1
        assert result[0]['j_date'] == '1402/01/01'
        assert result[0]['price'] == 50000.0

    def test_parse_usd_history_empty(self, api_client):
        result = api_client.parse_usd_history("")
        assert result == []

    def test_parse_usd_history_invalid(self, api_client):
        result = api_client.parse_usd_history("invalid,data")
        assert result == []

    def test_parse_sector_index_history_valid(self, api_client):
        data = "1402/01/01,1000000,1000,0.1"
        result = api_client.parse_sector_index_history(data, '1')

        assert len(result) == 1
        assert result[0]['sector_id'] == '1'
        assert result[0]['j_date'] == '1402/01/01'
        assert result[0]['value'] == 1000000.0

    def test_parse_sector_index_history_empty(self, api_client):
        result = api_client.parse_sector_index_history("", '1')
        assert result == []

    def test_parse_sector_index_history_invalid(self, api_client):
        result = api_client.parse_sector_index_history("invalid,data", '1')
        assert result == []

    def test_make_request_success_json(self, api_client):
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.headers = {'content-type': 'application/json'}
            mock_response.json.return_value = {'test': 'data'}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = api_client._make_request("test_endpoint", {'param': 'value'})

            assert result == {'test': 'data'}
            mock_get.assert_called_once_with("http://www.tsetmc.com/tsev2/test_endpoint", params={'param': 'value'}, timeout=30)

    def test_make_request_success_text(self, api_client):
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.headers = {'content-type': 'text/plain'}
            mock_response.text = 'test response'
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            result = api_client._make_request("test_endpoint")

            assert result == 'test response'

    def test_make_request_retry_on_failure(self, api_client):
        with patch('requests.get') as mock_get, patch('time.sleep') as mock_sleep:
            mock_response = MagicMock()
            mock_response.headers = {'content-type': 'text/plain'}
            mock_response.text = 'success'
            mock_response.raise_for_status.return_value = None
            mock_get.side_effect = [requests.exceptions.ConnectionError("Connection failed"), mock_response]

            result = api_client._make_request("test_endpoint")

            assert result == 'success'
            assert mock_get.call_count == 2
            mock_sleep.assert_called_once_with(1)

    def test_make_request_max_retries_exceeded(self, api_client):
        with patch('requests.get') as mock_get, patch('time.sleep') as mock_sleep:
            mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

            result = api_client._make_request("test_endpoint")

            assert result is None
            assert mock_get.call_count == 3
            assert mock_sleep.call_count == 2

    def test_make_request_timeout(self, api_client):
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.Timeout("Timeout")

            result = api_client._make_request("test_endpoint")

            assert result is None

    def test_make_request_http_error(self, api_client):
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Client Error")
            mock_get.return_value = mock_response

            result = api_client._make_request("test_endpoint")

            assert result is None

    def test_get_stock_list(self, api_client):
        with patch.object(api_client, '_make_request', return_value=[{'id': '1', 'name': 'Stock1'}]) as mock_make_request:
            result = api_client.get_stock_list()

            assert result == [{'id': '1', 'name': 'Stock1'}]
            mock_make_request.assert_called_once_with("api/Stock/GetStockList")

    def test_get_stock_details(self, api_client):
        with patch.object(api_client, '_make_request', return_value={'id': '123', 'name': 'Stock1'}) as mock_make_request:
            result = api_client.get_stock_details('123')

            assert result == {'id': '123', 'name': 'Stock1'}
            mock_make_request.assert_called_once_with("api/Stock/GetStockDetails/123")

    def test_get_current_date(self, api_client):
        with patch('api.tse_api.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 3, 21)
            result = api_client.get_current_date()

            assert result == "1403/03/21"

    def test_get_date_range(self, api_client):
        with patch('api.tse_api.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 3, 21)
            from_date, to_date = api_client.get_date_range(30)

            assert from_date == "1402/02/19"
            assert to_date == "1403/03/21"

    def test_parse_price_history_with_invalid_data(self, api_client):
        data = "1402/01/01,abc,1100,900,1050,1000000,1000000000,1000"
        result = api_client.parse_price_history(data, '123456')

        assert len(result) == 0  # Should skip invalid line

    def test_parse_client_type_history_with_invalid_data(self, api_client):
        data = "1402/01/01,abc,300000,500000000,300000000,500000,700000,500000000,700000000"
        result = api_client.parse_client_type_history(data, '123456')

        assert len(result) == 0  # Should skip invalid line

    def test_parse_index_history_with_invalid_data(self, api_client):
        data = "1402/01/01,abc,1000,0.1"
        result = api_client.parse_index_history(data, '123456')

        assert len(result) == 0  # Should skip invalid line

    def test_parse_shareholder_history_with_invalid_data(self, api_client):
        data = "123456789,سهامدار نمونه,abc,10.5"
        result = api_client.parse_shareholder_history(data, '123456', '1402/01/01')

        assert len(result) == 0  # Should skip invalid line

    def test_parse_intraday_trades_with_invalid_data(self, api_client):
        data = "09:00:00,abc,10000,10000000"
        result = api_client.parse_intraday_trades(data, '123456', '1402/01/01')

        assert len(result) == 0  # Should skip invalid line

    def test_parse_usd_history_with_invalid_data(self, api_client):
        data = "1402/01/01,abc,1000,2.0"
        result = api_client.parse_usd_history(data)

        assert len(result) == 0  # Should skip invalid line

    def test_parse_sector_index_history_with_invalid_data(self, api_client):
        data = "1402/01/01,abc,1000,0.1"
        result = api_client.parse_sector_index_history(data, '1')

        assert len(result) == 0  # Should skip invalid line
