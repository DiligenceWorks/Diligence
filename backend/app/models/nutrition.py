from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, DateTime, Boolean, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class NutritionGoal(Base):
    """Per-user macro + eating-window targets. One active per user."""
    __tablename__ = "nutrition_goals"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)

    # Macro targets (grams / kcal)
    calorie_target: Mapped[int] = mapped_column(Integer, default=2400)
    protein_g_target: Mapped[int] = mapped_column(Integer, default=180)
    fat_g_target: Mapped[int] = mapped_column(Integer, default=175)
    net_carbs_g_cap: Mapped[int] = mapped_column(Integer, default=20)  # strict keto

    # Training-day override (optional)
    training_calorie_target: Mapped[int | None] = mapped_column(Integer)
    training_protein_g_target: Mapped[int | None] = mapped_column(Integer)
    training_fat_g_target: Mapped[int | None] = mapped_column(Integer)

    # Eating window (24h local time, hours only)
    eating_window_start_hour: Mapped[int] = mapped_column(Integer, default=12)  # 12:00
    eating_window_end_hour: Mapped[int] = mapped_column(Integer, default=20)    # 20:00
    default_fast_hours: Mapped[int] = mapped_column(Integer, default=16)        # 16:8

    diet_style: Mapped[str] = mapped_column(String(30), default="strict_keto")
    timezone_str: Mapped[str] = mapped_column(String(50), default="Asia/Bangkok")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Fast(Base):
    """A single fasting bout — start/end + type + compliance flag."""
    __tablename__ = "fasts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    # Target length (hours) — 16, 18, 20, 24, 36, 48, 72
    target_hours: Mapped[int] = mapped_column(Integer, nullable=False)
    fast_type: Mapped[str] = mapped_column(String(20), default="daily")  # daily, weekly_24, long_48, long_72, extended

    # Completion state
    completed: Mapped[bool] = mapped_column(Boolean, default=False)  # hit target
    broken_early: Mapped[bool] = mapped_column(Boolean, default=False)  # ended before target

    # Points granted (for idempotency — don't double-credit)
    points_awarded: Mapped[int] = mapped_column(Integer, default=0)
    activity_log_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("activity_log.id"))

    notes: Mapped[str | None] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index("idx_fasts_user_started", "user_id", "started_at"),
    )


class ElectrolyteLog(Base):
    """Daily electrolyte dosing checklist — lightweight tracker."""
    __tablename__ = "electrolyte_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    log_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    sodium_mg: Mapped[int] = mapped_column(Integer, default=0)
    potassium_mg: Mapped[int] = mapped_column(Integer, default=0)
    magnesium_mg: Mapped[int] = mapped_column(Integer, default=0)

    notes: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        Index("idx_electrolyte_user_date", "user_id", "log_date"),
    )
