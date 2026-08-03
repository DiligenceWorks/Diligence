"""Timezone-aware date helpers.

All date calculations should use these helpers instead of date.today()
so the result reflects the user's local date, not the server's.
"""
from __future__ import annotations

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo


def _safe_tz(tz_str: str = "UTC"):
    """Resolve a timezone string to a tzinfo, falling back to UTC.

    Uses datetime.timezone.utc as the ultimate fallback in case
    tzdata is not installed (common on Windows).
    """
    try:
        return ZoneInfo(tz_str)
    except Exception:
        try:
            return ZoneInfo("UTC")
        except Exception:
            return timezone.utc


def today_for_user(tz_str: str = "UTC") -> date:
    """Return today's date in the user's timezone."""
    return datetime.now(_safe_tz(tz_str)).date()


def now_for_user(tz_str: str = "UTC") -> datetime:
    """Return the current datetime in the user's timezone (tz-aware)."""
    return datetime.now(_safe_tz(tz_str))


def day_start_utc(tz_str: str = "UTC") -> datetime:
    """Return the start of today (midnight) in the user's timezone, converted to UTC.

    Useful for database queries that store timestamps in UTC but need
    to filter by the user's local day.
    """
    user_today = today_for_user(tz_str)
    tz = _safe_tz(tz_str)
    local_midnight = datetime(user_today.year, user_today.month, user_today.day, tzinfo=tz)
    return local_midnight.astimezone(timezone.utc)


def get_week_boundaries(d: date | None = None, tz_str: str = "UTC") -> tuple[date, date]:
    """Return (Monday, Sunday) of the week containing date d.

    If d is None, uses today in the given timezone.
    """
    if d is None:
        d = today_for_user(tz_str)
    monday = d - __import__("datetime").timedelta(days=d.weekday())
    sunday = monday + __import__("datetime").timedelta(days=6)
    return monday, sunday
