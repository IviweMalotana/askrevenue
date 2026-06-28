"""Single source of truth for the analytics schema.

Used by three parts of the system so they never drift:

* the SQL safety validator (which tables are allowed),
* the NL->SQL prompt (grounding the model in real columns), and
* the schema explorer UI.

Only the analytics star schema is described here. The app's own tables
(saved_questions, dashboards, ...) are deliberately excluded — generated SQL is
never allowed to touch them.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Column:
    name: str
    type: str
    description: str
    enum: tuple[str, ...] | None = None


@dataclass(frozen=True)
class Table:
    name: str
    kind: str  # "dimension" | "fact"
    description: str
    columns: tuple[Column, ...]


SCHEMA: tuple[Table, ...] = (
    Table(
        name="dim_customer",
        kind="dimension",
        description="One row per customer account.",
        columns=(
            Column("customer_id", "integer", "Primary key.", None),
            Column("name", "text", "Customer / contact name.", None),
            Column("email", "text", "Contact email.", None),
            Column("country", "text", "ISO-3166 alpha-2 country code, e.g. 'US'.", None),
            Column(
                "segment", "text", "Go-to-market segment.",
                ("SMB", "Mid-Market", "Enterprise"),
            ),
            Column("signup_date", "date", "Date the customer first signed up.", None),
        ),
    ),
    Table(
        name="dim_plan",
        kind="dimension",
        description="Subscription plans available to purchase.",
        columns=(
            Column("plan_id", "integer", "Primary key.", None),
            Column(
                "plan_name", "text", "Plan tier name.",
                ("Starter", "Pro", "Business", "Enterprise"),
            ),
            Column(
                "billing_interval", "text", "How often the plan bills.",
                ("monthly", "annual"),
            ),
            Column("price_amount", "numeric", "Price charged per billing interval (USD).", None),
            Column(
                "monthly_price", "numeric",
                "Price normalised to a single month — use this for MRR.", None,
            ),
            Column("currency", "text", "ISO currency code (always 'USD' in this dataset).", None),
            Column("is_active", "boolean", "Whether the plan is currently sold.", None),
        ),
    ),
    Table(
        name="fact_subscription",
        kind="fact",
        description="One row per subscription. The grain for MRR and active-base questions.",
        columns=(
            Column("subscription_id", "integer", "Primary key.", None),
            Column("customer_id", "integer", "FK -> dim_customer.customer_id.", None),
            Column("plan_id", "integer", "FK -> dim_plan.plan_id.", None),
            Column(
                "status", "text", "Current subscription status.",
                ("active", "trialing", "canceled", "past_due"),
            ),
            Column("start_date", "date", "Date the subscription started.", None),
            Column(
                "end_date", "date",
                "Date the subscription ended; NULL if still active.", None,
            ),
            Column(
                "mrr_amount", "numeric",
                "Monthly recurring revenue contributed by this subscription (USD).", None,
            ),
        ),
    ),
    Table(
        name="fact_payment",
        kind="fact",
        description="One row per invoice/payment attempt.",
        columns=(
            Column("payment_id", "integer", "Primary key.", None),
            Column("customer_id", "integer", "FK -> dim_customer.customer_id.", None),
            Column("subscription_id", "integer", "FK -> fact_subscription.subscription_id.", None),
            Column("invoice_id", "text", "Human-readable invoice reference.", None),
            Column("amount", "numeric", "Payment amount (USD).", None),
            Column("currency", "text", "ISO currency code.", None),
            Column(
                "status", "text", "Outcome of the payment.",
                ("succeeded", "failed", "refunded"),
            ),
            Column(
                "failure_reason", "text",
                "Why a payment failed; NULL unless status = 'failed'.",
                (
                    "insufficient_funds", "card_declined", "expired_card",
                    "processing_error", "fraud_suspected",
                ),
            ),
            Column("payment_date", "date", "Date the payment was attempted.", None),
        ),
    ),
    Table(
        name="fact_churn",
        kind="fact",
        description="One row per churn (cancellation) event.",
        columns=(
            Column("churn_id", "integer", "Primary key.", None),
            Column("customer_id", "integer", "FK -> dim_customer.customer_id.", None),
            Column("subscription_id", "integer", "FK -> fact_subscription.subscription_id.", None),
            Column("plan_id", "integer", "FK -> dim_plan.plan_id (plan at time of churn).", None),
            Column("churn_date", "date", "Date the subscription churned.", None),
            Column(
                "reason", "text", "Stated/derived churn reason.",
                (
                    "too_expensive", "missing_features", "switched_competitor",
                    "no_longer_needed", "poor_support", "payment_failed",
                ),
            ),
            Column(
                "is_voluntary", "boolean",
                "True for customer-initiated churn; False for involuntary (payment) churn.",
                None,
            ),
            Column("mrr_lost", "numeric", "MRR lost when this subscription churned (USD).", None),
        ),
    ),
)


ALLOWED_TABLES: frozenset[str] = frozenset(t.name for t in SCHEMA)


def schema_as_dict() -> list[dict]:
    """Serialisable form for the API / schema explorer."""
    return [
        {
            "name": t.name,
            "kind": t.kind,
            "description": t.description,
            "columns": [
                {
                    "name": c.name,
                    "type": c.type,
                    "description": c.description,
                    "enum": list(c.enum) if c.enum else None,
                }
                for c in t.columns
            ],
        }
        for t in SCHEMA
    ]


def schema_prompt() -> str:
    """Compact textual schema for grounding the NL->SQL model."""
    lines: list[str] = []
    for t in SCHEMA:
        lines.append(f"TABLE {t.name} ({t.kind}) -- {t.description}")
        for c in t.columns:
            enum = f" [one of: {', '.join(c.enum)}]" if c.enum else ""
            lines.append(f"  {c.name} {c.type}{enum} -- {c.description}")
        lines.append("")
    return "\n".join(lines).strip()
