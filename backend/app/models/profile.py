import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy import String, Boolean, Integer, Numeric, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True)

    # Phase 1
    primary_goal: Mapped[str | None] = mapped_column(String(50))
    ttm_stage: Mapped[str | None] = mapped_column(String(20))

    # Phase 2 - Body
    age: Mapped[int | None] = mapped_column(Integer)
    height_cm: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
    weight_kg: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))
    gender: Mapped[str | None] = mapped_column(String(20))

    # PAR-Q+
    parq_heart_condition: Mapped[bool] = mapped_column(Boolean, default=False)
    parq_joint_issues: Mapped[bool] = mapped_column(Boolean, default=False)
    parq_medications: Mapped[bool] = mapped_column(Boolean, default=False)
    parq_other_conditions: Mapped[str | None] = mapped_column(Text)
    parq_cleared: Mapped[bool] = mapped_column(Boolean, default=True)

    # BREQ-2 motivation
    motivation_external: Mapped[Decimal | None] = mapped_column(Numeric(3, 1))
    motivation_introjected: Mapped[Decimal | None] = mapped_column(Numeric(3, 1))
    motivation_identified: Mapped[Decimal | None] = mapped_column(Numeric(3, 1))
    motivation_intrinsic: Mapped[Decimal | None] = mapped_column(Numeric(3, 1))
    motivation_amotivation: Mapped[Decimal | None] = mapped_column(Numeric(3, 1))
    motivation_rai: Mapped[Decimal | None] = mapped_column(Numeric(5, 1))

    # Preferences
    activity_preferences: Mapped[dict] = mapped_column(JSONB, default=list)
    equipment_access: Mapped[str | None] = mapped_column(String(50))
    days_per_week: Mapped[int] = mapped_column(Integer, default=3)
    minutes_per_session: Mapped[int] = mapped_column(Integer, default=30)

    # Completion
    phase1_completed: Mapped[bool] = mapped_column(Boolean, default=False)
    phase2_completed: Mapped[bool] = mapped_column(Boolean, default=False)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    user: Mapped["User"] = relationship(back_populates="profile")
