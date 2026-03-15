from __future__ import annotations

import uuid
from datetime import datetime, date, timezone
from decimal import Decimal
from sqlalchemy import String, Numeric, Date, DateTime, Text, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base


class FoodLog(Base):
    __tablename__ = "food_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    meal_type: Mapped[str] = mapped_column(String(20), nullable=False)
    food_name: Mapped[str] = mapped_column(String(300), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(200))
    barcode: Mapped[str | None] = mapped_column(String(50))
    serving_size: Mapped[str | None] = mapped_column(String(100))
    servings: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=1)
    calories: Mapped[Decimal | None] = mapped_column(Numeric(7, 1))
    protein_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 1))
    carbs_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 1))
    fat_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 1))
    fiber_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 1))
    sodium_mg: Mapped[Decimal | None] = mapped_column(Numeric(7, 1))
    sugar_g: Mapped[Decimal | None] = mapped_column(Numeric(6, 1))
    food_date: Mapped[date] = mapped_column(Date, nullable=False)
    logged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    off_product_id: Mapped[str | None] = mapped_column(String(50))
    off_data: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        Index("idx_food_log_user_date", "user_id", "food_date"),
    )
