"""Natural-language -> SQL generation via the Anthropic Claude API.

Grounded in the real schema (app/schema_def.py) and constrained to emit a single
read-only SELECT plus a chart proposal. The output is constrained with structured
outputs so we get well-formed JSON back without brittle parsing.

The summary is generated in a second pass *after* the query has run, so it can
describe the actual numbers rather than guessing from the question alone.
"""

from __future__ import annotations

import json

import anthropic

from app.config import get_settings
from app.schema_def import schema_prompt

settings = get_settings()

# JSON schema for the NL->SQL plan (structured outputs). All objects set
# additionalProperties:false, as required by the API.
_PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "sql": {
            "type": "string",
            "description": "A single read-only PostgreSQL SELECT statement.",
        },
        "chart_type": {
            "type": "string",
            "enum": ["line", "bar", "pie", "area"],
        },
        "chart_config": {
            "type": "object",
            "properties": {
                "x": {"type": "string", "description": "Column for the category/x-axis."},
                "y": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "One or more numeric measure columns.",
                },
            },
            "required": ["x", "y"],
            "additionalProperties": False,
        },
        "title": {"type": "string", "description": "Short chart title (<= 6 words)."},
    },
    "required": ["sql", "chart_type", "chart_config", "title"],
    "additionalProperties": False,
}

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
"""


class LLMError(RuntimeError):
    """Raised when the model call fails or returns unusable output."""


_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    return _client


def generate_plan(question: str, error_feedback: str | None = None) -> dict:
    """Return {sql, chart_type, chart_config, title} for a NL question.

    `error_feedback`, when provided, asks the model to repair a previous attempt
    that failed validation or execution.
    """
    user = question.strip()
    if error_feedback:
        user += (
            f"\n\nYour previous SQL failed with this error:\n{error_feedback}\n"
            "Return corrected SQL that satisfies the rules."
        )

    try:
        resp = _get_client().messages.create(
            model=settings.anthropic_model,
            max_tokens=1500,
            system=_SYSTEM,
            messages=[{"role": "user", "content": user}],
            output_config={"format": {"type": "json_schema", "schema": _PLAN_SCHEMA}},
        )
    except anthropic.APIError as e:
        raise LLMError(f"Claude API error: {e}") from e

    text = next((b.text for b in resp.content if b.type == "text"), None)
    if not text:
        raise LLMError("Model returned no content.")
    try:
        plan = json.loads(text)
    except json.JSONDecodeError as e:
        raise LLMError("Model returned malformed JSON.") from e
    return plan


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
        resp = _get_client().messages.create(
            model=settings.anthropic_model,
            max_tokens=400,
            system=(
                "You are a concise analyst. Given a question and the query result, "
                "write ONE short paragraph (2-4 sentences) describing what the data "
                "shows: the headline number or trend, and one notable detail. Use "
                "plain business English. Quote specific figures. No preamble, no "
                "bullet points, no markdown."
            ),
            messages=[{"role": "user", "content": json.dumps(payload, default=str)}],
        )
    except anthropic.APIError as e:
        raise LLMError(f"Claude API error: {e}") from e

    text = next((b.text for b in resp.content if b.type == "text"), "")
    return text.strip()
