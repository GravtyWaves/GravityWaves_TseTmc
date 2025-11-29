import pytest
import tempfile
import os
import json
from datetime import datetime
from utils.helpers import (
    clean_persian_text, normalize_ticker, parse_jalali_date, format_jalali_date,
    validate_web_id, validate_sector_code, safe_float_convert, safe_int_convert,
    calculate_percentage_change, group_data_by_date, filter_data_by_date_range,
    calculate_moving_average, detect_outliers, save_json_to_file, load_json_from_file,
    chunk_list, merge_dicts, get_nested_value
)


class TestTextProcessing:
    def test_clean_persian_text_normal(self):
        text = "  متن   فارسی  با  فاصله‌های  زیاد  "
        result = clean_persian_text(text)
        assert result == "متن فارسی با فاصله‌های زیاد"

    def test_clean_persian_text_empty(self):
        assert clean_persian_text("") == ""
        assert clean_persian_text(None) == ""

    def test_clean_persian_text_control_chars(self):
        text = "متن\x00با\x1fکاراکترهای\u007fکنترل"
        result = clean_persian_text(text)
        assert "\x00" not in result
        assert "\x1f" not in result
        assert "\u007f" not in result

    def test_normalize_ticker_normal(self):
        assert normalize_ticker("ABC1") == "ABC1"
        assert normalize_ticker("abc") == "ABC"

    def test_normalize_ticker_special_chars(self):
        assert normalize_ticker("A-B.C_1!") == "ABC1"

    def test_normalize_ticker_empty(self):
        assert normalize_ticker("") == ""
        assert normalize_ticker(None) == ""


class TestDateProcessing:
    def test_parse_jalali_date_valid(self):
        result = parse_jalali_date("1402/01/01")
        assert result is not None
        assert result.year == 2023  # 1402 + 621 = 2023

    def test_parse_jalali_date_invalid_format(self):
        assert parse_jalali_date("1402-01-01") is None
        assert parse_jalali_date("1402/01") is None
        assert parse_jalali_date("invalid") is None
        assert parse_jalali_date("") is None

    def test_parse_jalali_date_edge_cases(self):
        # Test with different months
        result = parse_jalali_date("1402/12/30")
        assert result is not None

    def test_format_jalali_date(self):
        date = datetime(2023, 3, 21)
        result = format_jalali_date(date)
        assert result == "1402/03/21"

    def test_format_jalali_date_edge_cases(self):
        # Test with different dates
        date = datetime(2023, 1, 1)
        result = format_jalali_date(date)
        assert result == "1401/01/01"


class TestValidation:
    def test_validate_web_id_valid(self):
        assert validate_web_id("123456") is True
        assert validate_web_id("0") is True

    def test_validate_web_id_invalid(self):
        assert validate_web_id("") is False
        assert validate_web_id("abc") is False
        assert validate_web_id("12.34") is False
        assert validate_web_id(None) is False

    def test_validate_sector_code_valid(self):
        assert validate_sector_code(1.0) is True
        assert validate_sector_code(123.45) is True

    def test_validate_sector_code_invalid(self):
        assert validate_sector_code(0.0) is False
        assert validate_sector_code(-1.0) is False
        assert validate_sector_code("invalid") is False
        assert validate_sector_code(None) is False


class TestTypeConversion:
    def test_safe_float_convert_valid(self):
        assert safe_float_convert("123.45") == 123.45
        assert safe_float_convert("123,456.78") == 123456.78
        assert safe_float_convert(123.45) == 123.45

    def test_safe_float_convert_invalid(self):
        assert safe_float_convert("") is None
        assert safe_float_convert("abc") is None
        assert safe_float_convert(None) is None

    def test_safe_int_convert_valid(self):
        assert safe_int_convert("123") == 123
        assert safe_int_convert("123.0") == 123
        assert safe_int_convert("123,456") == 123456

    def test_safe_int_convert_invalid(self):
        assert safe_int_convert("") is None
        assert safe_int_convert("abc") is None
        assert safe_int_convert("12.34") is None
        assert safe_int_convert(None) is None


class TestCalculations:
    def test_calculate_percentage_change_normal(self):
        assert calculate_percentage_change(100, 120) == 20.0
        assert calculate_percentage_change(100, 80) == -20.0

    def test_calculate_percentage_change_zero_division(self):
        assert calculate_percentage_change(0, 100) is None

    def test_calculate_percentage_change_invalid(self):
        assert calculate_percentage_change("invalid", 100) is None
        assert calculate_percentage_change(100, "invalid") is None

    def test_calculate_moving_average_normal(self):
        data = [1, 2, 3, 4, 5, 6, 7]
        result = calculate_moving_average(data, 3)
        expected = [None, None, 2.0, 3.0, 4.0, 5.0, 6.0]
        assert result == expected

    def test_calculate_moving_average_small_data(self):
        data = [1, 2]
        result = calculate_moving_average(data, 5)
        assert result == [None, None]

    def test_detect_outliers_normal(self):
        data = [1, 2, 3, 4, 5, 100]  # 100 is an outlier
        result = detect_outliers(data, 2.0)
        assert result[-1] is True  # Last element should be detected as outlier

    def test_detect_outliers_no_variance(self):
        data = [5, 5, 5, 5]
        result = detect_outliers(data, 2.0)
        assert all(not r for r in result)

    def test_detect_outliers_small_data(self):
        data = [1]
        result = detect_outliers(data, 2.0)
        assert result == [False]


class TestDataProcessing:
    def test_group_data_by_date(self):
        data = [
            {"date": "2023-01-01", "value": 1},
            {"date": "2023-01-01", "value": 2},
            {"date": "2023-01-02", "value": 3}
        ]
        result = group_data_by_date(data)
        assert len(result["2023-01-01"]) == 2
        assert len(result["2023-01-02"]) == 1

    def test_group_data_by_date_custom_field(self):
        data = [
            {"custom_date": "2023-01-01", "value": 1},
            {"custom_date": "2023-01-02", "value": 2}
        ]
        result = group_data_by_date(data, "custom_date")
        assert "2023-01-01" in result
        assert "2023-01-02" in result

    def test_filter_data_by_date_range(self):
        data = [
            {"date": "1402/01/01", "value": 1},
            {"date": "1402/01/15", "value": 2},
            {"date": "1402/02/01", "value": 3}
        ]
        result = filter_data_by_date_range(data, "1402/01/01", "1402/01/31")
        assert len(result) == 2

    def test_filter_data_by_date_range_invalid_dates(self):
        data = [{"date": "1402/01/01", "value": 1}]
        result = filter_data_by_date_range(data, "invalid", "1402/01/31")
        assert result == data  # Should return all data if dates are invalid

    def test_chunk_list(self):
        data = [1, 2, 3, 4, 5, 6, 7]
        result = chunk_list(data, 3)
        assert result == [[1, 2, 3], [4, 5, 6], [7]]

    def test_chunk_list_empty(self):
        result = chunk_list([], 3)
        assert result == []

    def test_merge_dicts(self):
        d1 = {"a": 1, "b": 2}
        d2 = {"b": 3, "c": 4}
        result = merge_dicts(d1, d2)
        assert result == {"a": 1, "b": 3, "c": 4}

    def test_get_nested_value(self):
        data = {"a": {"b": {"c": "value"}}}
        result = get_nested_value(data, ["a", "b", "c"])
        assert result == "value"

    def test_get_nested_value_missing_key(self):
        data = {"a": {"b": "value"}}
        result = get_nested_value(data, ["a", "c"], "default")
        assert result == "default"

    def test_get_nested_value_invalid_structure(self):
        data = {"a": "not_dict"}
        result = get_nested_value(data, ["a", "b"], "default")
        assert result == "default"


class TestFileOperations:
    def test_save_and_load_json(self):
        test_data = {"key": "value", "number": 123, "list": [1, 2, 3]}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            # Test save
            result = save_json_to_file(test_data, temp_path)
            assert result is True

            # Test load
            loaded_data = load_json_from_file(temp_path)
            assert loaded_data == test_data

        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_save_json_invalid_path(self):
        # Use a path with invalid characters that cannot be created
        result = save_json_to_file({"test": "data"}, "C:\\invalid\\path\\with\\invalid<chars>:file.json")
        assert result is False

    def test_load_json_invalid_path(self):
        # Use a path with invalid characters that cannot exist
        result = load_json_from_file("C:\\invalid\\path\\with\\invalid<chars>:file.json")
        assert result is None

    def test_load_json_invalid_json(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("invalid json content")
            temp_path = f.name

        try:
            result = load_json_from_file(temp_path)
            assert result is None
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
