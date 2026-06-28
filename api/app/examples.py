"""Curated example questions.

These serve three purposes:

1. Seed the demo dashboard so the app is fully clickable on first run.
2. Power the "example questions" chips in the Ask view.
3. Act as the deterministic fallback library when no ANTHROPIC_API_KEY is set, so the
   deployed demo always works (graceful degradation of the NL->SQL path).

Every SQL string here is a single, read-only SELECT against the star schema and is
safe to expose verbatim — transparency is part of the product pitch.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Example:
    title: str
    question: str
    sql: str
    chart_type: str  # line | bar | pie | area
    chart_config: dict
    summary: str
    keywords: list[str] = field(default_factory=list)
    pinned: bool = False


EXAMPLES: list[Example] = [
    Example(
        title="MRR by month",
        question="What was MRR by month over the last 12 months?",
        sql="""
SELECT to_char(d.month, 'YYYY-MM')        AS month,
       ROUND(SUM(s.mrr_amount), 2)        AS mrr
FROM generate_series(
        date_trunc('month', CURRENT_DATE) - INTERVAL '11 months',
        date_trunc('month', CURRENT_DATE),
        INTERVAL '1 month'
     ) AS d(month)
JOIN fact_subscription s
  ON s.start_date <= (d.month + INTERVAL '1 month' - INTERVAL '1 day')
 AND (s.end_date IS NULL OR s.end_date >= d.month)
GROUP BY d.month
ORDER BY d.month;
""".strip(),
        chart_type="line",
        chart_config={"x": "month", "y": ["mrr"]},
        summary=(
            "Monthly recurring revenue across the trailing 12 months, summing the MRR "
            "of every subscription active in each month. The trend shows the net effect "
            "of new business, expansion, and churn."
        ),
        keywords=["mrr", "recurring", "revenue by month", "monthly recurring"],
        pinned=True,
    ),
    Example(
        title="New customers by month",
        question="How many new customers signed up each month in the last 12 months?",
        sql="""
SELECT to_char(date_trunc('month', signup_date), 'YYYY-MM') AS month,
       COUNT(*)                                             AS new_customers
FROM dim_customer
WHERE signup_date >= date_trunc('month', CURRENT_DATE) - INTERVAL '11 months'
GROUP BY 1
ORDER BY 1;
""".strip(),
        chart_type="bar",
        chart_config={"x": "month", "y": ["new_customers"]},
        summary=(
            "New customer sign-ups per month for the last year, a leading indicator of "
            "top-of-funnel growth before expansion and churn are taken into account."
        ),
        keywords=["new customers", "signups", "sign-ups", "acquisition", "growth"],
        pinned=True,
    ),
    Example(
        title="Active subscriptions by plan",
        question="How many active subscriptions are there per plan?",
        sql="""
SELECT p.plan_name,
       COUNT(*) AS active_subscriptions
FROM fact_subscription s
JOIN dim_plan p ON p.plan_id = s.plan_id
WHERE s.status = 'active'
GROUP BY p.plan_name
ORDER BY active_subscriptions DESC;
""".strip(),
        chart_type="bar",
        chart_config={"x": "plan_name", "y": ["active_subscriptions"]},
        summary=(
            "The distribution of currently active subscriptions across plan tiers, "
            "showing where the installed base is concentrated."
        ),
        keywords=["active subscriptions", "subscriptions by plan", "plan distribution"],
        pinned=True,
    ),
    Example(
        title="Churn by plan",
        question="Which plan churns the most?",
        sql="""
SELECT p.plan_name,
       COUNT(*)                    AS churned_subscriptions,
       ROUND(SUM(c.mrr_lost), 2)   AS mrr_lost
FROM fact_churn c
JOIN dim_plan p ON p.plan_id = c.plan_id
GROUP BY p.plan_name
ORDER BY churned_subscriptions DESC;
""".strip(),
        chart_type="bar",
        chart_config={"x": "plan_name", "y": ["churned_subscriptions"]},
        summary=(
            "Cancelled subscriptions and the recurring revenue lost, broken down by plan. "
            "Lower tiers typically churn at higher rates; higher tiers carry more MRR per loss."
        ),
        keywords=["churn", "churn by plan", "cancellations", "which plan churns"],
        pinned=True,
    ),
    Example(
        title="Failed payments by reason",
        question="Show failed payments by reason this quarter.",
        sql="""
SELECT failure_reason,
       COUNT(*) AS failed_payments
FROM fact_payment
WHERE status = 'failed'
  AND payment_date >= date_trunc('quarter', CURRENT_DATE)
GROUP BY failure_reason
ORDER BY failed_payments DESC;
""".strip(),
        chart_type="pie",
        chart_config={"x": "failure_reason", "y": ["failed_payments"]},
        summary=(
            "The mix of failure reasons behind declined payments this quarter. Insufficient "
            "funds and card declines usually dominate and are the best targets for dunning."
        ),
        keywords=["failed payments", "payment failures", "decline reason", "dunning"],
        pinned=True,
    ),
    Example(
        title="Revenue by plan",
        question="What was collected revenue by plan over the last 12 months?",
        sql="""
SELECT p.plan_name,
       ROUND(SUM(pay.amount), 2) AS revenue
FROM fact_payment pay
JOIN fact_subscription s ON s.subscription_id = pay.subscription_id
JOIN dim_plan p           ON p.plan_id = s.plan_id
WHERE pay.status = 'succeeded'
  AND pay.payment_date >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY p.plan_name
ORDER BY revenue DESC;
""".strip(),
        chart_type="bar",
        chart_config={"x": "plan_name", "y": ["revenue"]},
        summary=(
            "Total successfully collected payments by plan over the last 12 months — actual "
            "cash collected, as distinct from MRR run-rate."
        ),
        keywords=["revenue by plan", "collected revenue", "cash", "billings by plan"],
        pinned=False,
    ),
    Example(
        title="Customers by segment",
        question="How are customers distributed across segments?",
        sql="""
SELECT segment,
       COUNT(*) AS customers
FROM dim_customer
GROUP BY segment
ORDER BY customers DESC;
""".strip(),
        chart_type="pie",
        chart_config={"x": "segment", "y": ["customers"]},
        summary=(
            "The split of the customer base across SMB, Mid-Market, and Enterprise segments."
        ),
        keywords=["segment", "customer segments", "smb", "enterprise"],
        pinned=False,
    ),
    Example(
        title="Monthly churn rate",
        question="What is the monthly churn rate over the last 12 months?",
        sql="""
WITH months AS (
    SELECT generate_series(
        date_trunc('month', CURRENT_DATE) - INTERVAL '11 months',
        date_trunc('month', CURRENT_DATE),
        INTERVAL '1 month'
    ) AS month
),
active_start AS (
    SELECT m.month,
           COUNT(s.subscription_id) AS active_at_start
    FROM months m
    JOIN fact_subscription s
      ON s.start_date < m.month
     AND (s.end_date IS NULL OR s.end_date >= m.month)
    GROUP BY m.month
),
churned AS (
    SELECT m.month,
           COUNT(c.churn_id) AS churned_in_month
    FROM months m
    LEFT JOIN fact_churn c
      ON date_trunc('month', c.churn_date) = m.month
    GROUP BY m.month
)
SELECT to_char(a.month, 'YYYY-MM') AS month,
       ROUND(100.0 * c.churned_in_month / NULLIF(a.active_at_start, 0), 2) AS churn_rate_pct
FROM active_start a
JOIN churned c ON c.month = a.month
ORDER BY a.month;
""".strip(),
        chart_type="line",
        chart_config={"x": "month", "y": ["churn_rate_pct"]},
        summary=(
            "Logo churn rate per month: subscriptions cancelled in the month as a percentage "
            "of those active at its start. Lower and flatter is healthier."
        ),
        keywords=["churn rate", "monthly churn", "logo churn"],
        pinned=False,
    ),
]


def find_example(question: str) -> Example | None:
    """Best-effort keyword match used by the no-API-key fallback path."""
    q = question.lower()
    best: tuple[int, Example] | None = None
    for ex in EXAMPLES:
        score = sum(1 for kw in ex.keywords if kw in q)
        if score and (best is None or score > best[0]):
            best = (score, ex)
    return best[1] if best else None
