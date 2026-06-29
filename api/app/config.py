"""Application configuration, loaded from environment variables.

Two database URLs are used intentionally:

* ``DATABASE_URL``           — full-privilege connection used for migrations and seeding.
* ``READONLY_DATABASE_URL``  — least-privilege connection used to execute generated SQL.

If the read-only URL is not provided we fall back to the main URL so the app still
runs locally, but in any real deployment they MUST differ (see docker-compose.yml,
which provisions a dedicated ``askrevenue_ro`` role with SELECT-only grants).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Anchor the .env search at file locations so it works regardless of cwd.
# Order matters: later files override earlier ones, so api/.env (if present)
# wins over the project-root .env.
_API_DIR = Path(__file__).resolve().parent.parent
_PROJECT_ROOT = _API_DIR.parent
_ENV_FILES = (_PROJECT_ROOT / ".env", _API_DIR / ".env")


def _normalize_db_url(url: str | None) -> str | None:
    """Coerce a provider-supplied URL to the psycopg driver.

    Managed Postgres (Railway, Heroku, etc.) hand out `postgres://` or
    `postgresql://` URLs; SQLAlchemy needs the explicit `postgresql+psycopg://`
    driver. This makes those URLs work without manual editing.
    """
    if not url:
        return url
    if url.startswith("postgresql+"):
        return url
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url[len("postgresql://"):]
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url[len("postgres://"):]
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILES,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Database ---------------------------------------------------------
    database_url: str = (
        "postgresql+psycopg://askrevenue:askrevenue@localhost:5432/askrevenue"
    )
    readonly_database_url: str | None = None

    @field_validator("database_url", "readonly_database_url")
    @classmethod
    def _coerce_driver(cls, v: str | None) -> str | None:
        return _normalize_db_url(v)

    # --- Anthropic Claude / LLM ------------------------------------------
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-opus-4-8"

    # --- Query safety -----------------------------------------------------
    query_row_limit: int = 1000
    query_timeout_ms: int = 5000

    # --- App --------------------------------------------------------------
    cors_origins: str = "http://localhost:3000"
    environment: str = "development"

    @property
    def effective_readonly_url(self) -> str:
        return self.readonly_database_url or self.database_url

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def llm_enabled(self) -> bool:
        return bool(self.anthropic_api_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
