"""FastAPI application entrypoint."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import query as query_router

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


@app.get("/health", tags=["meta"])
def health() -> dict:
    """Liveness probe plus a hint about whether the live LLM path is enabled."""
    return {
        "status": "ok",
        "environment": settings.environment,
        "llm_enabled": settings.llm_enabled,
    }
