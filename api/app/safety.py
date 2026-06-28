"""SQL safety validation.

Generated SQL is never trusted. Before any query runs we parse it with sqlglot and
assert a strict set of invariants:

1. It parses (we reject anything sqlglot can't understand).
2. It is exactly ONE statement (blocks `...; DROP TABLE ...` stacking).
3. The root is a read query (SELECT / set-operation / leading CTE), never DML/DDL.
4. No forbidden node appears anywhere in the tree (INSERT/UPDATE/DELETE/DDL/etc.,
   including sqlglot's `Command` catch-all for anything it couldn't model).
5. Every referenced table is in the analytics allow-list (CTE names excepted). This
   keeps generated SQL away from the app's own tables and system catalogs.

This is validation-in-depth: even if a check were bypassed, the query still runs on a
SELECT-only Postgres role (see app/db.py and infra/db-init).
"""

from __future__ import annotations

import sqlglot
from sqlglot import exp

from app.schema_def import ALLOWED_TABLES

DIALECT = "postgres"

# Node types that must never appear. getattr guards keep this resilient across
# sqlglot versions that may rename or drop a class.
_FORBIDDEN_NAMES = [
    "Insert", "Update", "Delete", "Merge", "Create", "Drop", "Alter",
    "TruncateTable", "Truncate", "Grant", "Revoke", "Set", "SetItem", "Use",
    "Copy", "Command", "Into", "Transaction", "Commit", "Rollback",
    "Call", "Pragma", "AlterTable",
]
_FORBIDDEN: tuple[type, ...] = tuple(
    getattr(exp, name) for name in _FORBIDDEN_NAMES if hasattr(exp, name)
)

_ALLOWED_ROOTS: tuple[type, ...] = (
    exp.Select,
    exp.Union,
    exp.Intersect,
    exp.Except,
    exp.Subquery,
)


class SafetyError(ValueError):
    """Raised when SQL fails a safety invariant. The message is user-facing."""


def validate_sql(sql: str) -> str:
    """Validate `sql` and return the cleaned, single-statement SQL ready to execute.

    Raises SafetyError with a human-readable reason on any violation.
    """
    if not sql or not sql.strip():
        raise SafetyError("Query is empty.")

    try:
        statements = [s for s in sqlglot.parse(sql, dialect=DIALECT) if s is not None]
    except sqlglot.errors.ParseError as e:
        raise SafetyError(f"Could not parse SQL: {_first_line(str(e))}") from e

    if len(statements) == 0:
        raise SafetyError("No SQL statement found.")
    if len(statements) > 1:
        raise SafetyError(
            "Only a single statement is allowed; multiple statements were found."
        )

    root = statements[0]

    if not isinstance(root, _ALLOWED_ROOTS):
        raise SafetyError(
            "Only read-only SELECT queries are allowed "
            f"(got a {root.key.upper()} statement)."
        )

    # Walk the whole tree for any forbidden construct.
    for node in root.walk():
        if isinstance(node, _FORBIDDEN):
            raise SafetyError(
                f"Disallowed operation detected ({node.key.upper()}). "
                "Only read-only SELECT queries are permitted."
            )

    _check_tables(root)

    # Re-emit the validated query so what we run is exactly what we display.
    cleaned = root.sql(dialect=DIALECT, pretty=True)
    return cleaned


def _check_tables(root: exp.Expression) -> None:
    cte_names = {
        cte.alias_or_name.lower()
        for cte in root.find_all(exp.CTE)
        if cte.alias_or_name
    }

    for table in root.find_all(exp.Table):
        name = (table.name or "").lower()
        schema = (table.db or "").lower()

        if name in cte_names:
            continue  # reference to a CTE defined in this query

        if schema in {"pg_catalog", "information_schema"} or name.startswith("pg_"):
            raise SafetyError("Access to system catalogs is not allowed.")

        if name not in ALLOWED_TABLES:
            allowed = ", ".join(sorted(ALLOWED_TABLES))
            raise SafetyError(
                f"Table '{table.name}' is not queryable. "
                f"Allowed tables: {allowed}."
            )


def referenced_tables(sql: str) -> list[str]:
    """Best-effort list of allow-listed tables a query touches (for display)."""
    try:
        root = sqlglot.parse_one(sql, dialect=DIALECT)
    except sqlglot.errors.ParseError:
        return []
    names = {
        (t.name or "").lower()
        for t in root.find_all(exp.Table)
    }
    return sorted(n for n in names if n in ALLOWED_TABLES)


def _first_line(text: str) -> str:
    return text.strip().splitlines()[0] if text.strip() else text
