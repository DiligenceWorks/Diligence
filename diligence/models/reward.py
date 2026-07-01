from __future__ import annotations

import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, Integer, Boolean, Text, Date, DateTime, ForeignKey, Index, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship
from diligence.database import Base


class Reward(Base):
    __tablename__ = "rewards"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    point_cost: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="rewards")


class RewardRedemption(Base):
    __tablename__ = "reward_redemptions"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("users.id"), nullable=False)
    reward_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("rewards.id"), nullable=False)
    points_spent: Mapped[int] = mapped_column(Integer, nullable=False)
    redeemed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    redemption_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text)

    __table_args__ = (
        Index("idx_redemptions_user_date", "user_id", "redemption_date"),
    )
