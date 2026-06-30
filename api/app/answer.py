"""Orchestrates a natural-language question into a full answer.

Pipeline:
  question
    -> SQL plan         (Claude when ANTHROPIC_API_KEY is set; else curated fallback)
    -> safety + execute (one repair retry on the LLM path)
    -> chart normalize  (validate the model's proposal against real columns)
    -> data-aware summary
"""

from __future__ import annotations

from app.charts import normalize_chart
from app.config import get_settings
from app.examples import find_example
from app.executor import QueryExecutionError, run_query
from app.llm import LLMError, generate_plan, summarize
from app.safety import SafetyError

settings = get_settings()


class AnswerError(RuntimeError):
    """Raised when a question cannot be answered (maps to a 4xx in the router)."""


def answer_question(question: str) -> dict:
    question = (question or "").strip()
    if not question:
        raise AnswerError("Please enter a question.")

    if settings.llm_enabled:
        return _answer_with_llm(question)
    return _answer_with_fallback(question)


def _answer_with_llm(question: str) -> dict:
    try:
        plan = generate_plan(question)
    except LLMError as e:
        # If the model itself is unavailable, try the curated library as a net.
        fallback = _try_fallback(question)
        if fallback:
            return fallback
        raise AnswerError(str(e)) from e

    result, used_sql = _execute_with_repair(question, plan["sql"])

    chart_type, chart_config = normalize_chart(
        plan.get("chart_type"), plan.get("chart_config"), result["columns"], result["rows"]
    )

    summary = _safe_summary(question, result, chart_type)

    return {
        "question": question,
        "title": plan.get("title") or question,
        "summary": summary,
        "chart_type": chart_type,
        "chart_config": chart_config,
        "result": result,
        "source": "llm",
        "matched": True,
    }


def _execute_with_repair(question: str, sql: str) -> tuple[dict, str]:
    """Run sql; on safety/execution failure, ask the model to fix it once."""
    try:
        return run_query(sql), sql
    except (SafetyError, QueryExecutionError) as first_err:
        try:
            repaired = generate_plan(question, error_feedback=str(first_err))
        except LLMError as e:
            raise AnswerError(f"Could not produce valid SQL: {first_err}") from e
        try:
            return run_query(repaired["sql"]), repaired["sql"]
        except (SafetyError, QueryExecutionError) as second_err:
            raise AnswerError(
                f"The generated SQL could not be run safely: {second_err}"
            ) from second_err


def _safe_summary(question: str, result: dict, chart_type: str) -> str:
    try:
        return summarize(question, result["columns"], result["rows"], chart_type)
    except LLMError:
        # Non-fatal: the chart and SQL still stand on their own.
        return ""


def _answer_with_fallback(question: str) -> dict:
    answer = _try_fallback(question)
    if answer:
        return answer
    # No curated match and no live model — guide the user to examples.
    raise AnswerError(
        "Demo mode is running without an API key, so only the example questions "
        "are answerable. Pick one of the suggested questions to see a live result."
    )


def _try_fallback(question: str) -> dict | None:
    ex = find_example(question)
    if not ex:
        return None
    try:
        result = run_query(ex.sql)
    except (SafetyError, QueryExecutionError) as e:
        raise AnswerError(f"Example query failed: {e}") from e

    chart_type, chart_config = normalize_chart(
        ex.chart_type, ex.chart_config, result["columns"], result["rows"]
    )
    return {
        "question": question,
        "title": ex.title,
        "summary": ex.summary,
        "chart_type": chart_type,
        "chart_config": chart_config,
        "result": result,
        "source": "fallback",
        "matched": True,
    }


def example_chips() -> list[dict]:
    """Example questions for the Ask view, with stable ids for the UI."""
    from app.examples import EXAMPLES

    return [
        {"title": ex.title, "question": ex.question}
        for ex in EXAMPLES
    ]


__all__ = ["answer_question", "AnswerError", "example_chips"]
