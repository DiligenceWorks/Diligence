from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Text, Boolean, DateTime, ForeignKey, UniqueConstraint, Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from diligence.database import Base


class ProgramCatalog(Base):
    """Shared program definitions — one per program, reusable by all users."""
    __tablename__ = "program_catalog"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    source_url: Mapped[str | None] = mapped_column(Text)
    duration_weeks: Mapped[int | None] = mapped_column(Integer)
    frequency_per_week: Mapped[int | None] = mapped_column(Integer)
    equipment: Mapped[dict] = mapped_column(JSON, default=list)
    difficulty: Mapped[str | None] = mapped_column(String(20))
    category: Mapped[str | None] = mapped_column(String(50))
    progression_rules: Mapped[str | None] = mapped_column(Text)
    structured_data: Mapped[dict | None] = mapped_column(JSON)
    crawl_status: Mapped[str] = mapped_column(String(20), default="pending")
    crawl_error: Mapped[str | None] = mapped_column(Text)
    crawled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    workouts: Mapped[list["CatalogWorkout"]] = relationship(
        back_populates="catalog", cascade="all, delete-orphan",
        order_by="CatalogWorkout.week_number, CatalogWorkout.day_number"
    )


class CatalogWorkout(Base):
    """Individual workout within a catalog program."""
    __tablename__ = "catalog_workouts"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    catalog_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("program_catalog.id", ondelete="CASCADE"), nullable=False
    )
    week_number: Mapped[int] = mapped_column(Integer, nullable=False)
    day_number: Mapped[int] = mapped_column(Integer, nullable=False)
    workout_name: Mapped[str | None] = mapped_column(String(200))
    exercises: Mapped[dict] = mapped_column(JSON, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)
    rest_day: Mapped[bool] = mapped_column(Boolean, default=False)

    catalog: Mapped["ProgramCatalog"] = relationship(back_populates="workouts")

    __table_args__ = (
        UniqueConstraint("catalog_id", "week_number", "day_number", name="uq_catalog_week_day"),
    )


class CrawlQueue(Base):
    """Job queue for program research crawls."""
    __tablename__ = "crawl_queue"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    catalog_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("program_catalog.id"), nullable=True
    )
    search_query: Mapped[str] = mapped_column(String(500), nullable=False)
    priority: Mapped[str] = mapped_column(String(10), default="low")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    urls_to_crawl: Mapped[dict] = mapped_column(JSON, default=list)
    crawled_content: Mapped[str | None] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class WorkoutLog(Base):
    """Per-user workout completion tracking against catalog workouts."""
    __tablename__ = "workout_logs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False
    )
    program_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("programs.id"), nullable=False
    )
    catalog_workout_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("catalog_workouts.id"), nullable=False
    )
    week_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    exercises_completed: Mapped[dict | None] = mapped_column(JSON)
    points_earned: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str | None] = mapped_column(Text)
