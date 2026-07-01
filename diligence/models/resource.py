from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, Text, DateTime, Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column
from diligence.database import Base


class Resource(Base):
    __tablename__ = "resource_library"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    thumbnail_url: Mapped[str | None] = mapped_column(Text)
    goal_tags: Mapped[dict] = mapped_column(JSON, default=list)
    activity_tags: Mapped[dict] = mapped_column(JSON, default=list)
    equipment_needed: Mapped[str | None] = mapped_column(String(50))
    ttm_stages: Mapped[dict] = mapped_column(JSON, default=list)
    difficulty: Mapped[str | None] = mapped_column(String(20))
    duration_days: Mapped[int | None] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
