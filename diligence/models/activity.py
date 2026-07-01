from __future__ import annotations

import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, Integer, Text, Date, DateTime, ForeignKey, Index, Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column
from diligence.database import Base


class ActivityLog(Base):
    __tablename__ = "activity_log"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(Text)
    duration_minutes: Mapped[int | None] = mapped_column(Integer)
    source: Mapped[str] = mapped_column(String(30), default="manual")
    external_id: Mapped[str | None] = mapped_column(String(100))
    points_earned: Mapped[int] = mapped_column(Integer, default=0)
    rule_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("point_rules.id"), nullable=True)
    activity_date: Mapped[date] = mapped_column(Date, nullable=False)
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    program_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("programs.id"), nullable=True)
    program_day: Mapped[int | None] = mapped_column(Integer)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict)

    __table_args__ = (
        Index("idx_activity_log_user_date", "user_id", "activity_date"),
        Index("idx_activity_log_external", "source", "external_id"),
    )
