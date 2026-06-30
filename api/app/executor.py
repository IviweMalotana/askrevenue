"""Execute validated SQL on the read-only connection, safely and predictably.

Guarantees layered on top of safety.validate_sql:

* runs inside a read-only transaction on the least-privilege role,
* applies a per-statement timeout (SET LOCAL statement_timeout),
* fetches at most row_limit+1 rows so we can flag truncation without materialising
  an unbounded result,
* serialises Decimal/date/datetime into JSON-friendly values.
"""

from __future__ import annotations

import time
from datetime import date, datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.config import get_settings
from app.db import ROSessionLocal
from app.safety import referenced_tables, validate_sql

settings = get_settings()


class QueryExecutionError(RuntimeError):
    """Raised when a validated query fails at execution time (syntax, timeout, ...)."""


def _jsonable(value: Any) -> Any:
    if isinstance(value, Decimal):
        # Keep integers clean; floats for fractional values.
        return int(value) if value == value.to_integral_value() else float(value)
    if isinstance(value, datetime | date):
        return value.isoformat()
    return value


def run_query(sql: str) -> dict[str, Any]:
    """Validate, execute, and return a serialisable result dict.

    Raises safety.SafetyError (caller maps to 400) for unsafe SQL, and
    QueryExecutionError for runtime failures.
    """
    cleaned = validate_sql(sql)
    row_limit = settings.query_row_limit

    session = ROSessionLocal()
    started = time.perf_counter()
    try:
        # Bound execution time. SET LOCAL is scoped to this transaction.
        session.execute(text(f"SET LOCAL statement_timeout = {int(settings.query_timeout_ms)}"))
        result = session.execute(text(cleaned))
        columns = list(result.keys())
        fetched = result.fetchmany(row_limit + 1)
    except SQLAlchemyError as e:
        raise QueryExecutionError(_clean_db_error(e)) from e
    finally:
        # Never commit; this path is read-only by contract and by role.
        session.rollback()
        session.close()

    truncated = len(fetched) > row_limit
    rows = [
        {col: _jsonable(val) for col, val in zip(columns, row, strict=True)}
        for row in fetched[:row_limit]
    ]

    duration_ms = int((time.perf_counter() - started) * 1000)
    return {
        "sql": cleaned,
        "columns": columns,
        "rows": rows,
        "row_count": len(rows),
        "truncated": truncated,
        "row_limit": row_limit,
        "duration_ms": duration_ms,
        "tables": referenced_tables(cleaned),
    }


def _clean_db_error(e: SQLAlchemyError) -> str:
    """Surface the useful part of a DB error without leaking internals."""
    orig = getattr(e, "orig", None)
    msg = str(orig) if orig else str(e)
    first = msg.strip().splitlines()[0] if msg.strip() else "Query failed."
    if "statement timeout" in msg.lower():
        return f"Query exceeded the {settings.query_timeout_ms} ms time limit."
    return first
