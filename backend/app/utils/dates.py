from datetime import date, timedelta


def get_week_boundaries(d: date) -> tuple[date, date]:
    """Return Monday and Sunday of the week containing date d."""
    monday = d - timedelta(days=d.weekday())
    sunday = monday + timedelta(days=6)
    return monday, sunday


def get_month_boundaries(year: int, month: int) -> tuple[date, date]:
    """Return first and last day of a month."""
    first = date(year, month, 1)
    if month == 12:
        last = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last = date(year, month + 1, 1) - timedelta(days=1)
    return first, last
