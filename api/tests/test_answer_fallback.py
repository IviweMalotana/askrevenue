"""End-to-end fallback path (no API key). Requires a seeded database."""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.answer import AnswerError, answer_question, example_chips
from app.db import ROSessionLocal


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


def test_fallback_matches_example(monkeypatch):
    # Force fallback mode regardless of environment.
    import app.answer as ans

    monkeypatch.setattr(ans.settings, "kimi_api_key", None, raising=False)

    answer = answer_question("which plan churns most?")
    assert answer["source"] == "fallback"
    assert answer["matched"] is True
    assert answer["result"]["row_count"] >= 1
    assert answer["chart_type"] in {"line", "bar", "pie", "area"}
    assert "plan_name" in answer["result"]["columns"]


def test_fallback_miss_raises(monkeypatch):
    import app.answer as ans

    monkeypatch.setattr(ans.settings, "kimi_api_key", None, raising=False)

    with pytest.raises(AnswerError):
        answer_question("what is the airspeed velocity of an unladen swallow?")


def test_example_chips_present():
    chips = example_chips()
    assert len(chips) >= 5
    assert all("title" in c and "question" in c for c in chips)
