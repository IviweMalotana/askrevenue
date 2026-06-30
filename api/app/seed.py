"""Seed a realistic subscription-business dataset.

Runs a month-by-month simulation over the trailing ~24 months so that the resulting
data tells a coherent story: steady top-of-funnel growth, expansion, tier-dependent
churn, and a believable mix of payment failures. The goal is data that makes charts
*mean something* — not random noise.

Idempotent: truncates the analytics + app tables and rebuilds them. Safe to re-run.

Usage:  uv run python -m app.seed
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import text

from app.dateutil_shim import add_months, month_floor
from app.db import SessionLocal, engine
from app.examples import EXAMPLES
from app.models import (
    Dashboard,
    DashboardItem,
    DimCustomer,
    DimPlan,
    FactChurn,
    FactPayment,
    FactSubscription,
    SavedQuestion,
)

RNG = random.Random(42)

# --- Simulation parameters -------------------------------------------------

MONTHS_OF_HISTORY = 24

SEGMENTS = ["SMB", "Mid-Market", "Enterprise"]
SEGMENT_WEIGHTS = [0.62, 0.27, 0.11]

# Plan tiers: (name, monthly_price). Annual variants get ~2 months free.
TIERS = [
    ("Starter", 29),
    ("Pro", 99),
    ("Business", 299),
    ("Enterprise", 999),
]

# Which tiers a segment tends to buy (weights aligned with TIERS order).
SEGMENT_TIER_WEIGHTS = {
    "SMB": [0.55, 0.35, 0.10, 0.00],
    "Mid-Market": [0.05, 0.45, 0.40, 0.10],
    "Enterprise": [0.00, 0.10, 0.45, 0.45],
}

# Monthly voluntary churn hazard by tier (lower tiers churn more).
TIER_MONTHLY_CHURN = {
    "Starter": 0.055,
    "Pro": 0.028,
    "Business": 0.015,
    "Enterprise": 0.008,
}

CHURN_REASONS_VOLUNTARY = [
    ("too_expensive", 0.28),
    ("missing_features", 0.22),
    ("switched_competitor", 0.18),
    ("no_longer_needed", 0.20),
    ("poor_support", 0.12),
]

FAILURE_REASONS = [
    ("insufficient_funds", 0.40),
    ("card_declined", 0.24),
    ("expired_card", 0.18),
    ("processing_error", 0.11),
    ("fraud_suspected", 0.07),
]

COUNTRIES = ["US", "US", "US", "GB", "CA", "AU", "DE", "FR", "NL", "SE", "IN", "BR"]

FIRST_NAMES = [
    "Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Sam", "Jamie", "Avery",
    "Quinn", "Drew", "Cameron", "Reese", "Parker", "Skyler", "Hayden", "Emerson",
    "Rowan", "Sasha", "Devon", "Noah", "Mia", "Liam", "Ava", "Ethan", "Sofia",
]
LAST_NAMES = [
    "Okafor", "Nguyen", "Patel", "Garcia", "Mueller", "Rossi", "Andersson", "Kovac",
    "Silva", "Haddad", "Yamamoto", "Novak", "Dubois", "Bauer", "Costa", "Larsson",
    "Khan", "Mbeki", "Johansson", "Ferreira", "Wagner", "Moreau", "Schneider",
]
COMPANY_SUFFIX = ["Labs", "Systems", "Group", "Digital", "Works", "Cloud", "io", "HQ", "Collective"]
COMPANY_ROOT = [
    "North", "Bright", "Cedar", "Quanta", "Vertex", "Lumen", "Harbor", "Atlas",
    "Pivot", "Cobalt", "Summit", "Meridian", "Orbit", "Forge", "Beacon", "Delta",
]


def weighted_choice(pairs: list[tuple[str, float]]) -> str:
    items, weights = zip(*pairs, strict=True)
    return RNG.choices(items, weights=weights, k=1)[0]


@dataclass
class PlanRow:
    plan_id: int
    name: str
    interval: str
    price_amount: float
    monthly_price: float


def build_plans() -> list[PlanRow]:
    plans: list[PlanRow] = []
    pid = 1
    for name, monthly in TIERS:
        plans.append(PlanRow(pid, name, "monthly", float(monthly), float(monthly)))
        pid += 1
        annual = round(monthly * 12 * 0.83, 2)  # ~17% annual discount
        plans.append(PlanRow(pid, name, "annual", annual, round(annual / 12, 2)))
        pid += 1
    return plans


def cohort_size(month_index: int, total_months: int) -> int:
    """Sign-ups grow over time with seasonal wobble."""
    base = 12 + int(28 * (month_index / max(total_months - 1, 1)))  # 12 -> ~40
    wobble = RNG.randint(-4, 6)
    return max(5, base + wobble)


def main() -> None:
    plans = build_plans()
    monthly_plans = {p.name: p for p in plans if p.interval == "monthly"}
    annual_plans = {p.name: p for p in plans if p.interval == "annual"}

    today = date.today()
    sim_start = month_floor(add_months(today, -MONTHS_OF_HISTORY))

    customers: list[dict] = []
    subscriptions: list[dict] = []
    payments: list[dict] = []
    churns: list[dict] = []

    cust_id = 0
    sub_id = 0
    pay_id = 0
    churn_id = 0
    invoice_seq = 0

    months = [month_floor(add_months(sim_start, i)) for i in range(MONTHS_OF_HISTORY + 1)]

    for m_idx, cohort_month in enumerate(months):
        if cohort_month > month_floor(today):
            break
        for _ in range(cohort_size(m_idx, len(months))):
            cust_id += 1
            segment = RNG.choices(SEGMENTS, weights=SEGMENT_WEIGHTS, k=1)[0]
            # Sign-up day within the cohort month.
            signup = cohort_month + timedelta(days=RNG.randint(0, 27))
            if signup > today:
                continue

            fn = RNG.choice(FIRST_NAMES)
            ln = RNG.choice(LAST_NAMES)
            company = f"{RNG.choice(COMPANY_ROOT)}{RNG.choice(COMPANY_SUFFIX)}"
            email = f"{fn.lower()}.{ln.lower()}@{company.lower().replace(' ', '')}.com"
            customers.append(
                dict(
                    customer_id=cust_id,
                    name=f"{fn} {ln}",
                    email=email,
                    country=RNG.choice(COUNTRIES),
                    segment=segment,
                    signup_date=signup,
                )
            )

            # Pick a plan tier appropriate to the segment.
            tier_weights = SEGMENT_TIER_WEIGHTS[segment]
            tier_name = RNG.choices([t[0] for t in TIERS], weights=tier_weights, k=1)[0]
            interval = "annual" if RNG.random() < 0.28 else "monthly"
            plan = (annual_plans if interval == "annual" else monthly_plans)[tier_name]

            sub_id += 1
            start_date = signup
            mrr = plan.monthly_price

            # Month-by-month survival simulation.
            churned_on: date | None = None
            churn_reason: str | None = None
            is_voluntary = True
            cursor = month_floor(start_date)
            while cursor <= month_floor(today):
                # Trial period in the first ~14 days; no churn during trial.
                tenure_months = max(
                    0,
                    (cursor.year - start_date.year) * 12 + cursor.month - start_date.month,
                )
                if tenure_months >= 1:
                    hazard = TIER_MONTHLY_CHURN[tier_name]
                    # Early-tenure customers churn a little more.
                    if tenure_months <= 2:
                        hazard *= 1.6
                    if RNG.random() < hazard:
                        churn_day = cursor + timedelta(days=RNG.randint(1, 27))
                        if churn_day <= today:
                            churned_on = churn_day
                            # ~15% of churn is involuntary (payment failure driven).
                            if RNG.random() < 0.15:
                                is_voluntary = False
                                churn_reason = "payment_failed"
                            else:
                                churn_reason = weighted_choice(CHURN_REASONS_VOLUNTARY)
                        break
                cursor = add_months(cursor, 1)

            end_date = churned_on
            # Determine current status.
            if churned_on is not None:
                status = "canceled"
            elif (today - start_date).days <= 14:
                status = "trialing"
            else:
                status = "active"

            subscriptions.append(
                dict(
                    subscription_id=sub_id,
                    customer_id=cust_id,
                    plan_id=plan.plan_id,
                    status=status,
                    start_date=start_date,
                    end_date=end_date,
                    mrr_amount=mrr,
                )
            )

            if churned_on is not None:
                churn_id += 1
                churns.append(
                    dict(
                        churn_id=churn_id,
                        customer_id=cust_id,
                        subscription_id=sub_id,
                        plan_id=plan.plan_id,
                        churn_date=churned_on,
                        reason=churn_reason,
                        is_voluntary=is_voluntary,
                        mrr_lost=mrr,
                    )
                )

            # Generate invoices/payments for each billing cycle until churn/now.
            billing_end = end_date or today
            if interval == "annual":
                cycle = start_date
                while cycle <= billing_end:
                    pay_id += 1
                    invoice_seq += 1
                    _emit_payment(
                        payments, pay_id, cust_id, sub_id, invoice_seq,
                        plan.price_amount, cycle, status, RNG,
                    )
                    cycle = add_months(cycle, 12)
            else:
                cycle = start_date
                while cycle <= billing_end:
                    pay_id += 1
                    invoice_seq += 1
                    _emit_payment(
                        payments, pay_id, cust_id, sub_id, invoice_seq,
                        plan.price_amount, cycle, status, RNG,
                    )
                    cycle = add_months(cycle, 1)

    _write(plans, customers, subscriptions, payments, churns)
    print(
        f"Seeded: {len(plans)} plans, {len(customers)} customers, "
        f"{len(subscriptions)} subscriptions, {len(payments)} payments, "
        f"{len(churns)} churn events."
    )


def _emit_payment(payments, pay_id, cust_id, sub_id, invoice_seq, amount, when, status, rng):
    r = rng.random()
    if r < 0.06:
        pay_status = "failed"
        reason = weighted_choice(FAILURE_REASONS)
    elif r < 0.08:
        pay_status = "refunded"
        reason = None
    else:
        pay_status = "succeeded"
        reason = None
    payments.append(
        dict(
            payment_id=pay_id,
            customer_id=cust_id,
            subscription_id=sub_id,
            invoice_id=f"INV-{when.year}-{invoice_seq:06d}",
            amount=amount,
            currency="USD",
            status=pay_status,
            failure_reason=reason,
            payment_date=when,
        )
    )


def _write(plans, customers, subscriptions, payments, churns) -> None:
    with engine.begin() as conn:
        conn.execute(
            text(
                "TRUNCATE dashboard_items, dashboards, saved_questions, "
                "fact_churn, fact_payment, fact_subscription, "
                "dim_customer, dim_plan RESTART IDENTITY CASCADE"
            )
        )

    session = SessionLocal()
    try:
        session.bulk_insert_mappings(
            DimPlan,
            [
                dict(
                    plan_id=p.plan_id,
                    plan_name=p.name,
                    billing_interval=p.interval,
                    price_amount=p.price_amount,
                    monthly_price=p.monthly_price,
                    currency="USD",
                    is_active=True,
                )
                for p in plans
            ],
        )
        session.bulk_insert_mappings(DimCustomer, customers)
        session.bulk_insert_mappings(FactSubscription, subscriptions)
        session.bulk_insert_mappings(FactPayment, payments)
        session.bulk_insert_mappings(FactChurn, churns)
        session.commit()

        _seed_app_content(session)
        session.commit()
    finally:
        session.close()


def _seed_app_content(session) -> None:
    """Seed saved questions and a default dashboard from the curated examples."""
    counts: dict[str, int] = defaultdict(int)
    saved_by_title: dict[str, SavedQuestion] = {}
    for ex in EXAMPLES:
        sq = SavedQuestion(
            title=ex.title,
            question_text=ex.question,
            generated_sql=ex.sql,
            chart_type=ex.chart_type,
            chart_config=json.dumps(ex.chart_config),
            summary=ex.summary,
            is_pinned=ex.pinned,
        )
        session.add(sq)
        saved_by_title[ex.title] = sq
        counts["saved"] += 1
    session.flush()

    dashboard = Dashboard(
        name="Revenue Overview",
        slug="revenue-overview",
        description="Core subscription health metrics — MRR, growth, churn, and payments.",
    )
    session.add(dashboard)
    session.flush()

    position = 0
    for ex in EXAMPLES:
        if ex.pinned:
            session.add(
                DashboardItem(
                    dashboard_id=dashboard.id,
                    saved_question_id=saved_by_title[ex.title].id,
                    position=position,
                )
            )
            position += 1


if __name__ == "__main__":
    main()
