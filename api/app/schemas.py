"""Pydantic request/response models for the API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    sql: str = Field(..., description="A single read-only SELECT statement.")


class QueryResult(BaseModel):
    sql: str = Field(..., description="The validated SQL that was actually executed.")
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    truncated: bool = Field(
        False, description="True if the result was capped at the row limit."
    )
    row_limit: int
    duration_ms: int
    tables: list[str] = Field(
        default_factory=list, description="Allow-listed tables the query touched."
    )


class ChartConfig(BaseModel):
    x: str | None = None
    y: list[str] = Field(default_factory=list)
    series: str | None = None


class AskRequest(BaseModel):
    question: str = Field(..., description="A plain-English analytics question.")


class AnswerResponse(BaseModel):
    question: str
    title: str
    summary: str | None = None
    chart_type: str
    chart_config: ChartConfig
    result: QueryResult
    source: str = Field(..., description="'llm' | 'fallback'")
    matched: bool = True


class ExampleChip(BaseModel):
    title: str
    question: str
