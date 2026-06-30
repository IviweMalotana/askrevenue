"""Endpoints for validating and executing read-only SQL."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.executor import QueryExecutionError, run_query
from app.safety import SafetyError, validate_sql
from app.schemas import QueryRequest, QueryResult

router = APIRouter(prefix="/api", tags=["query"])


@router.post("/query", response_model=QueryResult)
def execute_query(req: QueryRequest) -> QueryResult:
    """Validate `sql` is a safe single SELECT, run it read-only, and return rows."""
    try:
        result = run_query(req.sql)
    except SafetyError as e:
        raise HTTPException(
            status_code=400, detail={"kind": "unsafe_sql", "message": str(e)}
        ) from e
    except QueryExecutionError as e:
        raise HTTPException(
            status_code=400, detail={"kind": "execution_error", "message": str(e)}
        ) from e
    return QueryResult(**result)


@router.post("/validate")
def validate_only(req: QueryRequest) -> dict:
    """Check SQL safety without executing it (used for the transparency UI)."""
    try:
        cleaned = validate_sql(req.sql)
    except SafetyError as e:
        return {"valid": False, "message": str(e)}
    return {"valid": True, "sql": cleaned}
