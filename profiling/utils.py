import base64

from dateutil import parser
from datetime import date
from typing import Optional, Union


def _decode_base64url(data: str) -> str:
    """Decode base64url-encoded string safely."""
    try:
        padded = data + '=' * (-len(data) % 4)  # Correct padding
        decoded_bytes = base64.urlsafe_b64decode(padded)
        return decoded_bytes.decode('utf-8', errors='replace')
    except Exception:
        return ''
        
def _build_date_range_query(start_date, end_date):
    """
    Build a Gmail API query string for filtering by date range.
    Args:
        start_date (datetime.date or None): Inclusive start date.
        end_date (datetime.date or None): Exclusive end date.
    Returns:   
        str: Query string for Gmail API.
    """
    query_parts = []
    if start_date:
        query_parts.append(f'after:{start_date.strftime("%Y-%m-%d")}')
    if end_date:
        query_parts.append(f'before:{end_date.strftime("%Y-%m-%d")}')
    return ' '.join(query_parts)

def _to_date(date_or_str: Optional[Union[date, str]]) -> Optional[date]:
    """
    Convert input to a datetime.date object if possible.

    Args:
        date_or_str: date object or string representing a date.

    Returns:
        datetime.date or None if input is None.
    """
    if date_or_str is None:
        return None
    if isinstance(date_or_str, date):
        return date_or_str
    if isinstance(date_or_str, str):
        dt = parser.parse(date_or_str)
        return dt.date()
    raise ValueError(f"Unsupported date type: {type(date_or_str)}")