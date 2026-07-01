from __future__ import annotations

import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, Integer, Text, Date, DateTime, ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from diligence.database import Base


class Program(Base):
    __tablename__ = "programs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    source: Mapped[str | None] = mapped_column(String(50))
    source_url: Mapped[str | None] = mapped_column(Text)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="active")
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    # v2: Link to catalog program
    catalog_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("program_catalog.id"), nullable=True
    )
    current_week: Mapped[int] = mapped_column(Integer, default=1)
    current_day: Mapped[int] = mapped_column(Integer, default=1)

    user: Mapped["User"] = relationship(back_populates="programs")
