"""SQLAlchemy engines and session factories.

* ``engine`` / ``SessionLocal``    — read-write, used by migrations, seeding, and the
  application's own tables (saved questions, dashboards).
* ``ro_engine`` / ``ROSessionLocal`` — read-only, used exclusively to run user-generated
  SQL. The engine is created lazily so the app boots even if the RO role is absent.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings

settings = get_settings()


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, future=True)


# Read-only engine: a separate pool that connects with the least-privilege role.
ro_engine = create_engine(
    settings.effective_readonly_url,
    pool_pre_ping=True,
    future=True,
    # Defence in depth: even on the RO pool, mark every transaction read-only.
    execution_options={"postgresql_readonly": True},
)
ROSessionLocal = sessionmaker(
    bind=ro_engine, autocommit=False, autoflush=False, future=True
)


def get_db():
    """FastAPI dependency: a read-write session for the app's own tables."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
