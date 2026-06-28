"""The safety validator is the core of the product pitch — test it hard."""

from __future__ import annotations

import pytest

from app.safety import SafetyError, referenced_tables, validate_sql

VALID = [
    "SELECT 1",
    "SELECT customer_id, name FROM dim_customer LIMIT 10",
    "SELECT plan_name, COUNT(*) FROM fact_subscription s "
    "JOIN dim_plan p ON p.plan_id = s.plan_id GROUP BY plan_name",
    # Leading CTE.
    "WITH t AS (SELECT plan_id FROM dim_plan) SELECT * FROM t",
    # Set operation.
    "SELECT country FROM dim_customer UNION SELECT country FROM dim_customer",
    # Subquery in FROM.
    "SELECT * FROM (SELECT * FROM fact_payment) x LIMIT 5",
]


@pytest.mark.parametrize("sql", VALID)
def test_valid_selects_pass(sql):
    cleaned = validate_sql(sql)
    assert "select" in cleaned.lower()


UNSAFE = [
    ("", "empty"),
    ("   ", "empty"),
    ("INSERT INTO dim_plan (plan_id) VALUES (1)", "select"),
    ("UPDATE dim_customer SET name = 'x'", "select"),
    ("DELETE FROM dim_customer", "select"),
    ("DROP TABLE dim_customer", "select"),
    ("TRUNCATE dim_customer", "select"),
    ("ALTER TABLE dim_customer ADD COLUMN x int", "select"),
    ("CREATE TABLE evil (id int)", "select"),
    ("GRANT SELECT ON dim_customer TO public", None),
    # Statement stacking.
    ("SELECT 1; DROP TABLE dim_customer", "single statement"),
    ("SELECT 1; SELECT 2", "single statement"),
    # System catalogs / app tables / unknown tables.
    ("SELECT * FROM pg_catalog.pg_tables", "system catalog"),
    ("SELECT * FROM information_schema.tables", "system catalog"),
    ("SELECT * FROM saved_questions", "not queryable"),
    ("SELECT * FROM dashboards", "not queryable"),
    ("SELECT * FROM users", "not queryable"),
]


@pytest.mark.parametrize("sql,needle", UNSAFE)
def test_unsafe_sql_rejected(sql, needle):
    with pytest.raises(SafetyError) as exc:
        validate_sql(sql)
    if needle:
        assert needle.lower() in str(exc.value).lower()


def test_generate_series_table_function_allowed():
    sql = (
        "SELECT to_char(d.month, 'YYYY-MM') AS month, COUNT(*) AS n "
        "FROM generate_series(date_trunc('month', CURRENT_DATE) - INTERVAL '11 months', "
        "date_trunc('month', CURRENT_DATE), INTERVAL '1 month') AS d(month) "
        "JOIN fact_subscription s ON s.start_date <= d.month GROUP BY d.month"
    )
    validate_sql(sql)


def test_dangerous_table_function_rejected():
    with pytest.raises(SafetyError) as exc:
        validate_sql("SELECT * FROM pg_read_file('/etc/passwd')")
    assert "not allowed" in str(exc.value).lower()


def test_cte_reference_not_treated_as_table():
    sql = (
        "WITH active AS (SELECT * FROM fact_subscription WHERE status = 'active') "
        "SELECT COUNT(*) FROM active"
    )
    # `active` is a CTE, not a real table — must be allowed.
    validate_sql(sql)


def test_referenced_tables():
    sql = (
        "SELECT * FROM fact_payment p "
        "JOIN dim_customer c ON c.customer_id = p.customer_id"
    )
    assert referenced_tables(sql) == ["dim_customer", "fact_payment"]
