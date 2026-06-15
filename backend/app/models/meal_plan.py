"""Meal plan models — plans, items, and compliance tracking."""
from __future__ import annotations

import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy import String, Integer, Date, DateTime, Text, ForeignKey, DECIMAL
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class MealPlan(Base):
    __tablename__ = "meal_plans"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    diet_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    daily_calories: Mapped[int | None] = mapped_column(Integer, nullable=True)
    daily_protein_g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    daily_carbs_g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    daily_fat_g: Mapped[int | None] = mapped_column(Integer, nullable=True)
    restrictions: Mapped[dict] = mapped_column(JSONB, default=list)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    items: Mapped[list["MealPlanItem"]] = relationship(back_populates="plan", cascade="all, delete-orphan", lazy="selectin")


class MealPlanItem(Base):
    __tablename__ = "meal_plan_items"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("meal_plans.id", ondelete="CASCADE"), nullable=False)
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)
    meal_type: Mapped[str] = mapped_column(String(20), nullable=False)
    food_name: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    calories: Mapped[int | None] = mapped_column(Integer, nullable=True)
    protein_g: Mapped[Decimal | None] = mapped_column(DECIMAL(6, 1), nullable=True)
    carbs_g: Mapped[Decimal | None] = mapped_column(DECIMAL(6, 1), nullable=True)
    fat_g: Mapped[Decimal | None] = mapped_column(DECIMAL(6, 1), nullable=True)
    fiber_g: Mapped[Decimal | None] = mapped_column(DECIMAL(6, 1), nullable=True)
    serving_size: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    plan: Mapped["MealPlan"] = relationship(back_populates="items")


class MealCompliance(Base):
    __tablename__ = "meal_compliance"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("meal_plans.id"), nullable=False)
    plan_item_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    compliance_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)  # followed, substituted, skipped
    substitution: Mapped[str | None] = mapped_column(Text, nullable=True)
    food_log_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
