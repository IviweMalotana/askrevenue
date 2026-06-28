"""Chart-type inference and validation.

The LLM proposes a chart type and which columns map to axes, but we never trust that
blindly: we validate the proposal against the actual result columns and fall back to a
deterministic heuristic when the proposal is missing or nonsensical. This keeps the
visualisation sane even when the model is wrong.
"""

from __future__ import annotations

from typing import Any

VALID_CHART_TYPES = {"line", "bar", "pie", "area"}

_TEMPORAL_HINTS = ("month", "date", "day", "week", "quarter", "year", "period", "time")


def _is_number(v: Any) -> bool:
    return isinstance(v, int | float) and not isinstance(v, bool)


def _looks_temporal(name: str, values: list[Any]) -> bool:
    n = name.lower()
    if any(h in n for h in _TEMPORAL_HINTS):
        return True
    # YYYY-MM or ISO date-ish strings.
    for v in values[:5]:
        if isinstance(v, str) and len(v) >= 7 and v[:4].isdigit() and v[4] in "-/":
            return True
    return False


def infer_chart(columns: list[str], rows: list[dict]) -> tuple[str, dict]:
    """Pick a sensible chart type and axis mapping from the data alone."""
    if not columns:
        return "bar", {"x": None, "y": []}

    x = columns[0]
    col_values = {c: [r.get(c) for r in rows] for c in columns}

    numeric_cols = [
        c for c in columns[1:]
        if col_values[c] and all(v is None or _is_number(v) for v in col_values[c])
    ]
    # If nothing after the first column is numeric, treat the 2nd column as the measure.
    if not numeric_cols and len(columns) > 1:
        numeric_cols = [columns[1]]

    if _looks_temporal(x, col_values[x]):
        return "line", {"x": x, "y": numeric_cols}

    # Small categorical breakdown with a single measure -> pie reads best.
    if len(numeric_cols) == 1 and 2 <= len(rows) <= 6:
        return "pie", {"x": x, "y": numeric_cols}

    return "bar", {"x": x, "y": numeric_cols}


def normalize_chart(
    chart_type: str | None, chart_config: dict | None, columns: list[str], rows: list[dict]
) -> tuple[str, dict]:
    """Validate an LLM-proposed chart against real columns; repair if needed."""
    inferred_type, inferred_cfg = infer_chart(columns, rows)

    ct = (chart_type or "").lower()
    if ct not in VALID_CHART_TYPES:
        ct = inferred_type

    cfg = chart_config if isinstance(chart_config, dict) else {}
    x = cfg.get("x")
    y = cfg.get("y")
    if isinstance(y, str):
        y = [y]

    # x must be a real column; y must be a non-empty subset of real columns.
    if x not in columns:
        x = inferred_cfg["x"]
    if not isinstance(y, list) or not all(c in columns for c in y) or not y:
        y = inferred_cfg["y"]

    config = {"x": x, "y": y}
    if isinstance(cfg.get("series"), str) and cfg["series"] in columns:
        config["series"] = cfg["series"]

    return ct, config
