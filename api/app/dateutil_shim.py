"""Tiny month-arithmetic helpers (avoids a python-dateutil dependency)."""

from __future__ import annotations

from datetime import date


def add_months(d: date, months: int) -> date:
    month_index = d.month - 1 + months
    year = d.year + month_index // 12
    month = month_index % 12 + 1
    # Clamp the day to the last valid day of the target month.
    day = min(d.day, _days_in_month(year, month))
    return date(year, month, day)


def month_floor(d: date) -> date:
    return date(d.year, d.month, 1)


def _days_in_month(year: int, month: int) -> int:
    if month == 12:
        nxt = date(year + 1, 1, 1)
    else:
        nxt = date(year, month + 1, 1)
    return (nxt - date(year, month, 1)).days
