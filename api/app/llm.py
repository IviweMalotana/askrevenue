"""Natural-language -> SQL generation via Kimi (Moonshot AI).

Moonshot exposes an OpenAI-compatible Chat Completions API, so we use the
official `openai` SDK pointed at Moonshot's `base_url`. JSON mode guarantees
parseable JSON; we still validate the result's shape post-hoc because
`response_format={"type": "json_object"}` does NOT enforce a schema — the
schema lives in the system prompt as guidance.

The summary is generated in a second pass *after* the query has run, so it can
describe the actual numbers rather than guessing from the question alone.
"""

from __future__ import annotations

import json

from openai import APIError, OpenAI

from app.config import get_settings
from app.schema_def import schema_prompt

settings = get_settings()

_PLAN_SHAPE = """\
Return a single JSON object with this exact shape (no extra keys):
{
  "sql": "<one read-only PostgreSQL SELECT statement>",
  "chart_type": "<one of: line | bar | pie | area>",
  "chart_config": { "x": "<column name>", "y": ["<column name>", ...] },
  "title": "<short chart title, <= 6 words>"
}
"""

_SYSTEM = f"""\
You are a careful analytics engineer for a subscription business. Translate the
user's plain-English question into ONE read-only PostgreSQL SELECT statement over
the schema below, and propose how to visualise the result.

SCHEMA
{schema_prompt()}

HARD RULES
- Emit exactly one statement. It MUST be a SELECT (a leading CTE/WITH is fine).
- NEVER write to the database: no INSERT/UPDATE/DELETE/DDL, no transactions.
- Only reference the tables listed above. Never touch system catalogs.
- Use monthly_price (or fact_subscription.mrr_amount) for MRR, not price_amount.
- Prefer explicit JOINs on the documented foreign keys.
- Return human-friendly column aliases (e.g. "month", "mrr", "new_customers").
- For time series, format the period as text 'YYYY-MM' and ORDER BY the period.
- Keep result sets small and aggregated; this powers a chart, not a data dump.

CHART
- chart_config.x is the category/time column; chart_config.y lists numeric columns.
- line/area for trends over time, bar for category comparisons, pie for shares.
- Use column names exactly as they appear in your SELECT's output.

OUTPUT
{_PLAN_SHAPE}
"""


class LLMError(RuntimeError):
    """Raised when the model call fails or returns unusable output."""


_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(
            api_key=settings.kimi_api_key,
            base_url=settings.kimi_base_url,
        )
    return _client


def _validate_plan(obj: object) -> dict:
    """Make sure the model returned the shape we promised the rest of the app."""
    if not isinstance(obj, dict):
        raise LLMError("Model returned non-object JSON.")
    for key in ("sql", "chart_type", "chart_config", "title"):
        if key not in obj:
            raise LLMError(f"Model JSON is missing required field '{key}'.")
    if not isinstance(obj["sql"], str) or not obj["sql"].strip():
        raise LLMError("Model returned empty SQL.")
    cfg = obj["chart_config"]
    if not isinstance(cfg, dict) or "x" not in cfg or "y" not in cfg:
        raise LLMError("Model returned an invalid chart_config.")
    if not isinstance(cfg["y"], list):
        cfg["y"] = [cfg["y"]] if isinstance(cfg["y"], str) else []
    return obj


def generate_plan(question: str, error_feedback: str | None = None) -> dict:
    """Return {sql, chart_type, chart_config, title} for a NL question.

    `error_feedback`, when provided, asks the model to repair a previous attempt
    that failed validation or execution.
    """
    user = question.strip()
    if error_feedback:
        user += (
            f"\n\nYour previous SQL failed with this error:\n{error_feedback}\n"
            "Return corrected JSON with valid SQL."
        )

    try:
        resp = _get_client().chat.completions.create(
            model=settings.kimi_model,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
            max_tokens=1500,
            response_format={"type": "json_object"},
        )
    except APIError as e:
        raise LLMError(f"Kimi API error: {e}") from e

    text = (resp.choices[0].message.content or "").strip()
    if not text:
        raise LLMError("Model returned no content.")
    try:
        plan = json.loads(text)
    except json.JSONDecodeError as e:
        raise LLMError("Model returned malformed JSON.") from e
    return _validate_plan(plan)


def summarize(question: str, columns: list[str], rows: list[dict], chart_type: str) -> str:
    """One-paragraph, data-aware summary of a query result."""
    # Cap rows fed to the model so we stay cheap and within context.
    sample = rows[:50]
    payload = {
        "question": question,
        "chart_type": chart_type,
        "columns": columns,
        "rows": sample,
        "row_count": len(rows),
    }
    try:
        resp = _get_client().chat.completions.create(
            model=settings.kimi_model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a concise analyst. Given a question and the query result, "
                        "write ONE short paragraph (2-4 sentences) describing what the data "
                        "shows: the headline number or trend, and one notable detail. Use "
                        "plain business English. Quote specific figures. No preamble, no "
                        "bullet points, no markdown."
                    ),
                },
                {"role": "user", "content": json.dumps(payload, default=str)},
            ],
            temperature=0.4,
            max_tokens=400,
        )
    except APIError as e:
        raise LLMError(f"Kimi API error: {e}") from e

    return (resp.choices[0].message.content or "").strip()
