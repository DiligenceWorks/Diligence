"""Support chat router — user messaging + admin replies + Telegram notifications."""
from __future__ import annotations

import uuid as uuid_mod
from datetime import datetime, date, timezone, timedelta
from typing import Annotated

import httpx
import logging
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User
from app.models.support import SupportThread, SupportMessage
from app.models.activity import ActivityLog
from app.services.points_engine import get_active_program, get_today_status
from app.utils.auth import get_current_user
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/support", tags=["support"])

MAX_MESSAGES_PER_DAY = 10


# ── Schemas ─────────────────────────────────────────────────────────────────

class SendMessageRequest(BaseModel):
    body: str

class AdminReplyRequest(BaseModel):
    body: str


# ── Context Gathering ───────────────────────────────────────────────────────

async def gather_user_context(db: AsyncSession, user: User) -> dict:
    """Collect current user state for support context."""
    context = {
        "member_since": str(user.created_at.date()) if user.created_at else None,
    }

    try:
        program = await get_active_program(db, user.id)
        if program:
            context["program_name"] = program.get("name")
            context["program_day"] = program.get("day")
            context["program_total_days"] = program.get("total_days")
            day = program.get("day", 0)
            total = program.get("total_days", 1)
            context["program_completion_pct"] = round((day / total * 100) if total > 0 else 0, 1)
    except Exception:
        pass

    try:
        status = await get_today_status(db, user.id)
        context["points_today"] = status.get("points_earned", 0)
        context["daily_target"] = status.get("daily_minimum", 80)
        context["gate_passed"] = status.get("gate_passed", False)
    except Exception:
        pass

    try:
        result = await db.execute(
            select(ActivityLog)
            .where(ActivityLog.user_id == user.id, ActivityLog.category == "workout")
            .order_by(ActivityLog.logged_at.desc())
            .limit(1)
        )
        last = result.scalar_one_or_none()
        if last:
            context["last_workout"] = f"{last.activity_date} — {last.title or 'Workout'}"
    except Exception:
        pass

    return context


# ── Telegram Notification ──────────────────────────────────────────────────

def format_telegram_message(user_name: str, message: str, context: dict) -> str:
    """Format the Telegram notification message."""
    lines = [f"🏋️ *Fitness Support*\n"]
    lines.append(f"From: *{user_name}*")

    prog = context.get("program_name")
    if prog:
        day = context.get("program_day", "?")
        total = context.get("program_total_days", "?")
        pct = context.get("program_completion_pct", 0)
        lines.append(f"Program: {prog} (Day {day}/{total} — {pct}%)")

    pts = context.get("points_today", 0)
    target = context.get("daily_target", 80)
    gate = "✅" if context.get("gate_passed") else "❌"
    lines.append(f"Points today: {pts}/{target} {gate}")

    last = context.get("last_workout")
    if last:
        lines.append(f"Last workout: {last}")

    lines.append(f"\n💬 \"{message}\"")
    lines.append(f"\n👉 {settings.base_url}/support/admin")

    return "\n".join(lines)


async def send_telegram_notification(user_name: str, message: str, context: dict):
    """Fire-and-forget Telegram notification. Never blocks or fails the request."""
    token = settings.telegram_bot_token
    chat_id = settings.telegram_chat_id

    if not token or not chat_id:
        logger.warning("Telegram credentials not configured — skipping notification")
        return

    text = format_telegram_message(user_name, message, context)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "Markdown",
                    "disable_web_page_preview": True,
                },
            )
            if resp.status_code != 200:
                logger.warning(f"Telegram send failed: {resp.status_code} {resp.text[:200]}")
    except Exception as e:
        logger.warning(f"Telegram notification error: {e}")


# ── Helper: Get or Create Thread ───────────────────────────────────────────

async def get_or_create_thread(db: AsyncSession, user_id: uuid_mod.UUID) -> SupportThread:
    """Get the user's support thread, creating one if it doesn't exist."""
    result = await db.execute(
        select(SupportThread)
        .options(selectinload(SupportThread.messages))
        .where(SupportThread.user_id == user_id)
    )
    thread = result.scalar_one_or_none()

    if not thread:
        thread = SupportThread(user_id=user_id)
        db.add(thread)
        await db.flush()
        # Re-fetch with messages loaded
        result = await db.execute(
            select(SupportThread)
            .options(selectinload(SupportThread.messages))
            .where(SupportThread.id == thread.id)
        )
        thread = result.scalar_one_or_none()

    return thread


# ── User Endpoints ─────────────────────────────────────────────────────────

@router.get("/thread")
async def get_thread(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get the user's support thread with all messages. Marks admin replies as read."""
    thread = await get_or_create_thread(db, user.id)

    # Mark admin messages as read
    if thread.unread_user > 0:
        now = datetime.now(timezone.utc)
        await db.execute(
            update(SupportMessage)
            .where(
                SupportMessage.thread_id == thread.id,
                SupportMessage.sender == "admin",
                SupportMessage.read_at.is_(None),
            )
            .values(read_at=now)
        )
        thread.unread_user = 0
        await db.flush()

    messages = [
        {
            "id": str(m.id),
            "sender": m.sender,
            "body": m.body,
            "created_at": m.created_at.isoformat(),
            "read_at": m.read_at.isoformat() if m.read_at else None,
        }
        for m in thread.messages
    ]

    return {
        "thread_id": str(thread.id),
        "messages": messages,
    }


@router.post("/messages")
async def send_message(
    req: SendMessageRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """User sends a support message. Auto-attaches context, fires Telegram notification."""
    body = req.body.strip()
    if not body:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    if len(body) > 2000:
        raise HTTPException(status_code=400, detail="Message too long (max 2000 characters)")

    # Rate limit check
    today_start = datetime.combine(date.today(), datetime.min.time(), tzinfo=timezone.utc)
    thread = await get_or_create_thread(db, user.id)

    result = await db.execute(
        select(func.count(SupportMessage.id)).where(
            SupportMessage.thread_id == thread.id,
            SupportMessage.sender == "user",
            SupportMessage.created_at >= today_start,
        )
    )
    count_today = result.scalar() or 0
    if count_today >= MAX_MESSAGES_PER_DAY:
        raise HTTPException(
            status_code=429,
            detail=f"Maximum {MAX_MESSAGES_PER_DAY} messages per day. Try again tomorrow."
        )

    # Gather context
    context = await gather_user_context(db, user)

    # Create message
    message = SupportMessage(
        thread_id=thread.id,
        sender="user",
        body=body,
        context=context,
    )
    db.add(message)
    thread.last_message_at = datetime.now(timezone.utc)
    thread.unread_admin += 1
    await db.flush()

    # Fire Telegram notification (non-blocking)
    display_name = getattr(user, "display_name", None) or user.username
    await send_telegram_notification(display_name, body, context)

    return {
        "id": str(message.id),
        "status": "sent",
        "message": "Message sent! We'll get back to you soon.",
    }


@router.get("/unread")
async def get_unread_count(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get unread count for the user (admin replies they haven't seen)."""
    result = await db.execute(
        select(SupportThread.unread_user).where(SupportThread.user_id == user.id)
    )
    count = result.scalar()
    return {"unread": count or 0}


# ── Admin Endpoints ────────────────────────────────────────────────────────

def require_admin(user: User):
    """Check that the user has admin privileges."""
    if not getattr(user, "is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")


@router.get("/admin/threads")
async def list_threads(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """List all support threads with last message preview. Admin only."""
    require_admin(user)

    result = await db.execute(
        select(SupportThread)
        .options(selectinload(SupportThread.messages))
        .order_by(SupportThread.last_message_at.desc())
    )
    threads = result.scalars().all()

    out = []
    for t in threads:
        # Get the user's display name
        from app.models.user import User as UserModel
        user_result = await db.execute(
            select(UserModel).where(UserModel.id == t.user_id)
        )
        thread_user = user_result.scalar_one_or_none()
        user_name = thread_user.display_name or thread_user.username if thread_user else "Unknown"

        last_msg = t.messages[-1] if t.messages else None

        out.append({
            "id": str(t.id),
            "user_id": str(t.user_id),
            "user_name": user_name,
            "unread_admin": t.unread_admin,
            "last_message": {
                "sender": last_msg.sender,
                "body": last_msg.body[:100] + ("..." if len(last_msg.body) > 100 else ""),
                "created_at": last_msg.created_at.isoformat(),
            } if last_msg else None,
            "message_count": len(t.messages),
        })

    return out


@router.get("/admin/threads/{thread_id}")
async def get_admin_thread(
    thread_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get full thread with messages and context. Marks user messages as read. Admin only."""
    require_admin(user)

    result = await db.execute(
        select(SupportThread)
        .options(selectinload(SupportThread.messages))
        .where(SupportThread.id == uuid_mod.UUID(thread_id))
    )
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    # Mark user messages as read
    if thread.unread_admin > 0:
        now = datetime.now(timezone.utc)
        await db.execute(
            update(SupportMessage)
            .where(
                SupportMessage.thread_id == thread.id,
                SupportMessage.sender == "user",
                SupportMessage.read_at.is_(None),
            )
            .values(read_at=now)
        )
        thread.unread_admin = 0
        await db.flush()

    # Get user info
    from app.models.user import User as UserModel
    user_result = await db.execute(
        select(UserModel).where(UserModel.id == thread.user_id)
    )
    thread_user = user_result.scalar_one_or_none()

    # Get latest context from the most recent user message
    latest_context = None
    for m in reversed(thread.messages):
        if m.sender == "user" and m.context:
            latest_context = m.context
            break

    messages = [
        {
            "id": str(m.id),
            "sender": m.sender,
            "body": m.body,
            "context": m.context if m.sender == "user" else None,
            "created_at": m.created_at.isoformat(),
            "read_at": m.read_at.isoformat() if m.read_at else None,
        }
        for m in thread.messages
    ]

    return {
        "thread_id": str(thread.id),
        "user_name": thread_user.display_name or thread_user.username if thread_user else "Unknown",
        "user_id": str(thread.user_id),
        "latest_context": latest_context,
        "messages": messages,
    }


@router.post("/admin/threads/{thread_id}/reply")
async def reply_to_thread(
    thread_id: str,
    req: AdminReplyRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Admin sends a reply to a user's support thread."""
    require_admin(user)

    body = req.body.strip()
    if not body:
        raise HTTPException(status_code=400, detail="Reply cannot be empty")

    result = await db.execute(
        select(SupportThread).where(SupportThread.id == uuid_mod.UUID(thread_id))
    )
    thread = result.scalar_one_or_none()
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")

    message = SupportMessage(
        thread_id=thread.id,
        sender="admin",
        body=body,
    )
    db.add(message)
    thread.last_message_at = datetime.now(timezone.utc)
    thread.unread_user += 1
    await db.flush()

    return {
        "id": str(message.id),
        "status": "sent",
    }
