"""AI coaching chat endpoint — SSE streaming responses."""
from __future__ import annotations

import json
import logging
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.utils.auth import get_current_user
from app.models.user import User
from app.services import ai_provider

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["AI Coaching"])


@router.post("/chat")
async def chat_with_ai(
    request: Request,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Stream an AI coaching response via SSE.

    Body: {"message": "...", "history": [{"role": "user"|"assistant", "content": "..."}]}
    Response: text/event-stream with data chunks.
    """
    body = await request.json()
    message = body.get("message", "").strip()
    history = body.get("history", [])

    if not message:
        return {"error": "Message cannot be empty"}

    # Validate history format
    clean_history = []
    for msg in history[-20:]:  # Cap at last 20 messages
        if isinstance(msg, dict) and msg.get("role") in ("user", "assistant") and msg.get("content"):
            clean_history.append({"role": msg["role"], "content": msg["content"][:4000]})

    async def event_stream():
        async for chunk in ai_provider.chat(user.id, message, clean_history, db):
            yield f"data: {json.dumps({'text': chunk})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/status")
async def ai_status(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Check which AI provider is configured."""
    provider = await ai_provider.get_active_ai_provider(db, user_id=user.id)
    if provider:
        return {
            "configured": True,
            "provider": provider["name"],
            "model": provider["model"],
        }
    return {"configured": False, "provider": None, "model": None}
