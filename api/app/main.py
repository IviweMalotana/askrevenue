"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import ask as ask_router
from app.routers import query as query_router
from app.routers import saved as saved_router
from app.schema_def import schema_as_dict

settings = get_settings()

app = FastAPI(
    title="AskRevenue API",
    description="Natural-language analytics over a subscription business.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(query_router.router)
app.include_router(ask_router.router)
app.include_router(saved_router.router)


@app.get("/health", tags=["meta"])
def health() -> dict:
    """Liveness probe plus a hint about whether the live LLM path is enabled."""
    return {
        "status": "ok",
        "environment": settings.environment,
        "llm_enabled": settings.llm_enabled,
    }


@app.get("/api/schema", tags=["meta"])
def get_schema() -> list[dict]:
    """The analytics schema the AI is allowed to query (for the schema explorer)."""
    return schema_as_dict()
