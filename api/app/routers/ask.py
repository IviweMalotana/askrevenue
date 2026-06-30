"""Natural-language question -> SQL + chart + summary."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.answer import AnswerError, answer_question, example_chips
from app.schemas import AnswerResponse, AskRequest, ExampleChip

router = APIRouter(prefix="/api", tags=["ask"])


@router.post("/ask", response_model=AnswerResponse)
def ask(req: AskRequest) -> AnswerResponse:
    """Answer a plain-English question with generated SQL, a chart, and a summary."""
    try:
        answer = answer_question(req.question)
    except AnswerError as e:
        raise HTTPException(
            status_code=422, detail={"kind": "unanswerable", "message": str(e)}
        ) from e
    return AnswerResponse(**answer)


@router.get("/examples", response_model=list[ExampleChip])
def examples() -> list[ExampleChip]:
    """Example questions for the Ask view's suggestion chips."""
    return [ExampleChip(**c) for c in example_chips()]
