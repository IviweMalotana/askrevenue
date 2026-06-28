"""Saved questions and the dashboard.

Saved questions persist a question + its generated SQL + chart config so they can
be re-run later. The dashboard renders every pinned question by re-executing its
stored SQL live (through the same safety + read-only pipeline), so charts always
reflect current data.
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.executor import QueryExecutionError, run_query
from app.models import SavedQuestion
from app.safety import SafetyError
from app.schemas import (
    DashboardItemOut,
    DashboardOut,
    PinUpdate,
    QueryResult,
    SavedQuestionCreate,
    SavedQuestionOut,
)

router = APIRouter(prefix="/api", tags=["saved"])


def _to_out(sq: SavedQuestion) -> SavedQuestionOut:
    cfg = json.loads(sq.chart_config) if sq.chart_config else {}
    return SavedQuestionOut(
        id=sq.id,
        title=sq.title,
        question_text=sq.question_text,
        generated_sql=sq.generated_sql,
        chart_type=sq.chart_type,
        chart_config=cfg,
        summary=sq.summary,
        is_pinned=sq.is_pinned,
    )


@router.get("/saved-questions", response_model=list[SavedQuestionOut])
def list_saved(db: Session = Depends(get_db)) -> list[SavedQuestionOut]:
    rows = db.scalars(
        select(SavedQuestion).order_by(SavedQuestion.updated_at.desc())
    ).all()
    return [_to_out(r) for r in rows]


@router.post("/saved-questions", response_model=SavedQuestionOut, status_code=201)
def create_saved(body: SavedQuestionCreate, db: Session = Depends(get_db)) -> SavedQuestionOut:
    sq = SavedQuestion(
        title=body.title.strip() or "Untitled",
        question_text=body.question_text,
        generated_sql=body.generated_sql,
        chart_type=body.chart_type,
        chart_config=json.dumps(body.chart_config.model_dump(exclude_none=True)),
        summary=body.summary,
        is_pinned=True,  # saving from the Ask view pins it to the dashboard by default
    )
    db.add(sq)
    db.commit()
    db.refresh(sq)
    return _to_out(sq)


@router.delete("/saved-questions/{sq_id}", status_code=204)
def delete_saved(sq_id: int, db: Session = Depends(get_db)) -> None:
    sq = db.get(SavedQuestion, sq_id)
    if not sq:
        raise HTTPException(status_code=404, detail="Saved question not found.")
    db.delete(sq)
    db.commit()


@router.post("/saved-questions/{sq_id}/pin", response_model=SavedQuestionOut)
def set_pin(sq_id: int, body: PinUpdate, db: Session = Depends(get_db)) -> SavedQuestionOut:
    sq = db.get(SavedQuestion, sq_id)
    if not sq:
        raise HTTPException(status_code=404, detail="Saved question not found.")
    sq.is_pinned = body.pinned
    db.commit()
    db.refresh(sq)
    return _to_out(sq)


@router.post("/saved-questions/{sq_id}/run", response_model=QueryResult)
def run_saved(sq_id: int, db: Session = Depends(get_db)) -> QueryResult:
    sq = db.get(SavedQuestion, sq_id)
    if not sq:
        raise HTTPException(status_code=404, detail="Saved question not found.")
    try:
        result = run_query(sq.generated_sql)
    except (SafetyError, QueryExecutionError) as e:
        raise HTTPException(
            status_code=400, detail={"kind": "execution_error", "message": str(e)}
        ) from e
    return QueryResult(**result)


@router.get("/dashboard", response_model=DashboardOut)
def get_dashboard(db: Session = Depends(get_db)) -> DashboardOut:
    """The default dashboard: every pinned question, executed live."""
    pinned = db.scalars(
        select(SavedQuestion)
        .where(SavedQuestion.is_pinned.is_(True))
        .order_by(SavedQuestion.updated_at.desc())
    ).all()

    items: list[DashboardItemOut] = []
    for sq in pinned:
        out = _to_out(sq)
        try:
            result = QueryResult(**run_query(sq.generated_sql))
            items.append(DashboardItemOut(saved_question=out, result=result))
        except (SafetyError, QueryExecutionError) as e:
            items.append(DashboardItemOut(saved_question=out, error=str(e)))

    return DashboardOut(
        name="Revenue Overview",
        description="Core subscription health metrics — MRR, growth, churn, and payments.",
        items=items,
    )
