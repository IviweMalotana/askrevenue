"""SQLAlchemy ORM models.

Analytics schema is a clean star: three dimension-ish anchors (customer, plan) and
three fact tables (subscription, payment, churn). Keeping it small and predictable
makes the LLM's generated SQL far more reliable.

Application schema (saved_questions, dashboards, dashboard_items) backs the product
itself and is never exposed to the read-only query path.
"""

from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

# ---------------------------------------------------------------------------
# Analytics star schema
# ---------------------------------------------------------------------------


class DimCustomer(Base):
    __tablename__ = "dim_customer"

    customer_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(200), nullable=False)
    country: Mapped[str] = mapped_column(String(2), nullable=False)
    # SMB / Mid-Market / Enterprise
    segment: Mapped[str] = mapped_column(String(20), nullable=False)
    signup_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DimPlan(Base):
    __tablename__ = "dim_plan"

    plan_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Starter / Pro / Business / Enterprise
    plan_name: Mapped[str] = mapped_column(String(40), nullable=False)
    # monthly / annual
    billing_interval: Mapped[str] = mapped_column(String(10), nullable=False)
    # price charged per billing interval
    price_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    # price normalised to a single month (for MRR)
    monthly_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class FactSubscription(Base):
    __tablename__ = "fact_subscription"

    subscription_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("dim_customer.customer_id"), nullable=False)
    plan_id: Mapped[int] = mapped_column(ForeignKey("dim_plan.plan_id"), nullable=False)
    # active / trialing / canceled / past_due
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    # monthly recurring revenue contribution
    mrr_amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FactPayment(Base):
    __tablename__ = "fact_payment"

    payment_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("dim_customer.customer_id"), nullable=False)
    subscription_id: Mapped[int] = mapped_column(
        ForeignKey("fact_subscription.subscription_id"), nullable=False
    )
    invoice_id: Mapped[str] = mapped_column(String(24), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # succeeded / failed / refunded
    failure_reason: Mapped[str | None] = mapped_column(String(40), nullable=True)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FactChurn(Base):
    __tablename__ = "fact_churn"

    churn_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("dim_customer.customer_id"), nullable=False)
    subscription_id: Mapped[int] = mapped_column(
        ForeignKey("fact_subscription.subscription_id"), nullable=False
    )
    plan_id: Mapped[int] = mapped_column(ForeignKey("dim_plan.plan_id"), nullable=False)
    churn_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str] = mapped_column(String(40), nullable=False)
    is_voluntary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    mrr_lost: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)


# ---------------------------------------------------------------------------
# Application schema
# ---------------------------------------------------------------------------


class SavedQuestion(Base):
    __tablename__ = "saved_questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    generated_sql: Mapped[str] = mapped_column(Text, nullable=False)
    chart_type: Mapped[str] = mapped_column(String(20), nullable=False, default="bar")
    chart_config: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON: {x, y[], ...}
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_pinned: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    items: Mapped[list[DashboardItem]] = relationship(
        back_populates="saved_question", cascade="all, delete-orphan"
    )


class Dashboard(Base):
    __tablename__ = "dashboards"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False, unique=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    items: Mapped[list[DashboardItem]] = relationship(
        back_populates="dashboard",
        cascade="all, delete-orphan",
        order_by="DashboardItem.position",
    )


class DashboardItem(Base):
    __tablename__ = "dashboard_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dashboard_id: Mapped[int] = mapped_column(
        ForeignKey("dashboards.id", ondelete="CASCADE"), nullable=False
    )
    saved_question_id: Mapped[int] = mapped_column(
        ForeignKey("saved_questions.id", ondelete="CASCADE"), nullable=False
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    dashboard: Mapped[Dashboard] = relationship(back_populates="items")
    saved_question: Mapped[SavedQuestion] = relationship(back_populates="items")
