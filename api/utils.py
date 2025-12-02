"""
Utility functions for data scraping operations.
"""

from datetime import datetime, date, timedelta
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


def validate_date_range(start_date: str, end_date: str) -> bool:
    """
    Validate date range for TSE API queries.

    Args:
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        True if valid range, False otherwise
    """


def get_business_days(start_date: date, end_date: date) -> List[date]:
    """
    Get list of business days between two dates (excluding weekends).

    Args:
        start_date: Start date
        end_date: End date

    Returns:
        List of business day dates
    """


def format_tse_date(date_obj: date) -> str:
    """
    Format date for TSE API (YYYYMMDD).

    Args:
        date_obj: Date object

    Returns:
        Formatted date string
    """


def parse_tse_date(date_str: str) -> Optional[date]:
    """
    Parse TSE date string to date object.

    Args:
        date_str: Date string in various formats

    Returns:
        Date object or None if parsing fails
    """


def get_sector_web_id(sector_name: str) -> Optional[str]:
    """
    Get web ID for a sector name.

    Args:
        sector_name: Name of the sector

    Returns:
        Sector web ID or None if not found
    """


def calculate_price_change_percentage(old_price: float, new_price: float) -> float:
    """
    Calculate price change percentage.

    Args:
        old_price: Previous price
        new_price: Current price

    Returns:
        Percentage change
    """
    if old_price == 0:
        return 0.0

    return ((new_price - old_price) / old_price) * 100


def safe_float_convert(value: Any) -> Optional[float]:
    """
    Safely convert value to float.

    Args:
        value: Value to convert

    Returns:
        Float value or None if conversion fails
    """
    try:
        if isinstance(value, str):
            # Remove commas and spaces
            value = value.replace(',', '').replace(' ', '')
        return float(value)
    except (ValueError, TypeError):
        return None


def safe_int_convert(value: Any) -> Optional[int]:
    """
    Safely convert value to int.

    Args:
        value: Value to convert

    Returns:
        Int value or None if conversion fails
    """
    try:
        if isinstance(value, str):
            # Remove commas and spaces
            value = value.replace(',', '').replace(' ', '')
        return int(float(value))  # Handle float strings
    except (ValueError, TypeError):
        return None


def chunk_list(data: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks of specified size.

    Args:
        data: List to chunk
        chunk_size: Size of each chunk

    Returns:
        List of chunks
    """
    return [data[i:i + chunk_size] for i in range(0, len(data), chunk_size)]


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge multiple dictionaries.

    Args:
        *dicts: Dictionaries to merge

    Returns:
        Merged dictionary
    """
    result = {}
    for d in dicts:
        result.update(d)
    return result
