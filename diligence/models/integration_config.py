"""Integration configuration model — encrypted credential storage."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from diligence.database import Base


class IntegrationConfig(Base):
    __tablename__ = "integration_configs"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    config_key: Mapped[str] = mapped_column(String(100), nullable=False)
    config_value: Mapped[str] = mapped_column(Text, nullable=False)  # Fernet encrypted
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint("user_id", "provider", "config_key", name="uq_integration_config"),
    )
