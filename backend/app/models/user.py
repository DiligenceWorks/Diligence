from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    timezone: Mapped[str] = mapped_column(String(50), default="Asia/Bangkok")

    # Relationships
    profile: Mapped["UserProfile"] = relationship(back_populates="user", uselist=False, lazy="selectin")
    programs: Mapped[list["Program"]] = relationship(back_populates="user", lazy="selectin")
    point_rules: Mapped[list["PointRule"]] = relationship(back_populates="user", lazy="selectin")
    rewards: Mapped[list["Reward"]] = relationship(back_populates="user", lazy="selectin")
