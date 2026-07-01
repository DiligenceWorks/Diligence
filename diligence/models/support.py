from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, Index, UniqueConstraint, Uuid, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from diligence.database import Base


class SupportThread(Base):
    """One thread per user — private conversation with admin."""
    __tablename__ = "support_threads"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), unique=True, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    last_message_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    unread_user: Mapped[int] = mapped_column(Integer, default=0)
    unread_admin: Mapped[int] = mapped_column(Integer, default=0)

    messages: Mapped[list["SupportMessage"]] = relationship(
        back_populates="thread", cascade="all, delete-orphan",
        order_by="SupportMessage.created_at"
    )


class SupportMessage(Base):
    """Individual message within a support thread."""
    __tablename__ = "support_messages"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    thread_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("support_threads.id", ondelete="CASCADE"), nullable=False
    )
    sender: Mapped[str] = mapped_column(String(10), nullable=False)  # 'user' or 'admin'
    body: Mapped[str] = mapped_column(Text, nullable=False)
    context: Mapped[dict | None] = mapped_column(JSON)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    thread: Mapped["SupportThread"] = relationship(back_populates="messages")

    __table_args__ = (
        Index("idx_support_messages_thread", "thread_id", "created_at"),
    )
