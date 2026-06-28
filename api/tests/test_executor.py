"""Executor tests. Require a running, seeded database; skipped otherwise."""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.db import ROSessionLocal
from app.executor import QueryExecutionError, run_query
from app.safety import SafetyError


def _db_available() -> bool:
    try:
        s = ROSessionLocal()
        s.execute(text("SELECT 1"))
        s.close()
        return True
    except SQLAlchemyError:
        return False


pytestmark = pytest.mark.skipif(
    not _db_available(), reason="read-only database not reachable"
)


def test_simple_aggregate():
    res = run_query(
        "SELECT segment, COUNT(*) AS n FROM dim_customer GROUP BY segment ORDER BY n DESC"
    )
    assert res["columns"][0] == "segment"
    assert res["row_count"] >= 1
    assert all("segment" in row and "n" in row for row in res["rows"])
    assert res["tables"] == ["dim_customer"]


def test_unsafe_sql_blocked_before_execution():
    with pytest.raises(SafetyError):
        run_query("UPDATE dim_customer SET name = 'x'")


def test_row_cap_truncates(monkeypatch):
    import app.executor as ex

    monkeypatch.setattr(ex.settings, "query_row_limit", 5, raising=False)
    res = run_query("SELECT * FROM fact_payment")
    assert res["row_count"] == 5
    assert res["truncated"] is True
    assert res["row_limit"] == 5


def test_statement_timeout(monkeypatch):
    import app.executor as ex

    monkeypatch.setattr(ex.settings, "query_timeout_ms", 250, raising=False)
    with pytest.raises(QueryExecutionError) as exc:
        run_query("SELECT pg_sleep(3)")
    assert "time limit" in str(exc.value).lower()


def test_numeric_and_date_serialisation():
    res = run_query(
        "SELECT mrr_amount, start_date FROM fact_subscription LIMIT 1"
    )
    row = res["rows"][0]
    assert isinstance(row["mrr_amount"], int | float)
    assert isinstance(row["start_date"], str)  # ISO date string
