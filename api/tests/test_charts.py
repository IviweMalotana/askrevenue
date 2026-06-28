"""Chart inference + normalization."""

from __future__ import annotations

from app.charts import infer_chart, normalize_chart


def test_temporal_first_column_is_line():
    cols = ["month", "mrr"]
    rows = [{"month": "2025-01", "mrr": 100}, {"month": "2025-02", "mrr": 120}]
    ct, cfg = infer_chart(cols, rows)
    assert ct == "line"
    assert cfg == {"x": "month", "y": ["mrr"]}


def test_small_category_single_measure_is_pie():
    cols = ["segment", "customers"]
    rows = [{"segment": "SMB", "customers": 5}, {"segment": "Enterprise", "customers": 3}]
    ct, _ = infer_chart(cols, rows)
    assert ct == "pie"


def test_many_categories_is_bar():
    cols = ["plan_name", "n"]
    rows = [{"plan_name": f"p{i}", "n": i} for i in range(10)]
    ct, _ = infer_chart(cols, rows)
    assert ct == "bar"


def test_normalize_repairs_bad_proposal():
    cols = ["month", "mrr"]
    rows = [{"month": "2025-01", "mrr": 100}]
    # Model proposed a nonexistent column and an invalid type.
    ct, cfg = normalize_chart("scatter", {"x": "nope", "y": ["alsonope"]}, cols, rows)
    assert ct in {"line", "bar", "pie", "area"}
    assert cfg["x"] in cols
    assert all(c in cols for c in cfg["y"])


def test_normalize_keeps_valid_proposal():
    cols = ["plan_name", "revenue"]
    rows = [{"plan_name": "Pro", "revenue": 10}]
    ct, cfg = normalize_chart("bar", {"x": "plan_name", "y": ["revenue"]}, cols, rows)
    assert ct == "bar"
    assert cfg == {"x": "plan_name", "y": ["revenue"]}
