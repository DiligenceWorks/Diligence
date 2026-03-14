import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class PointRule(Base):
    __tablename__ = "point_rules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    points: Mapped[int] = mapped_column(Integer, nullable=False)
    unit: Mapped[str | None] = mapped_column(String(20))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="point_rules")


class DailyTarget(Base):
    __tablename__ = "daily_targets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)
    daily_minimum_pts: Mapped[int] = mapped_column(Integer, default=80)
    weekly_target_pts: Mapped[int] = mapped_column(Integer, default=500)
    weekly_bonus_pts: Mapped[int] = mapped_column(Integer, default=50)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


# Default rules to create per user
DEFAULT_POINT_RULES = [
    {"category": "workout", "description": "Complete a workout", "points": 50, "unit": "per_completion"},
    {"category": "food_log", "description": "Log all meals for the day", "points": 30, "unit": "per_day"},
    {"category": "steps_target", "description": "Hit daily step/activity goal", "points": 20, "unit": "per_day"},
    {"category": "screen_free", "description": "Screen-free activity", "points": 20, "unit": "per_hour"},
    {"category": "daily_checkin", "description": "Complete daily check-in", "points": 10, "unit": "per_day"},
]

# Suggested targets by TTM stage
TTM_DAILY_TARGETS = {
    "precontemplation": {"daily_minimum_pts": 30, "weekly_target_pts": 150},
    "contemplation": {"daily_minimum_pts": 50, "weekly_target_pts": 250},
    "preparation": {"daily_minimum_pts": 80, "weekly_target_pts": 400},
    "action": {"daily_minimum_pts": 100, "weekly_target_pts": 600},
    "maintenance": {"daily_minimum_pts": 120, "weekly_target_pts": 700},
}
