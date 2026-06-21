"""Multi-provider AI coaching service.

Two code paths:
- OpenAI-compatible: covers OpenAI, OpenRouter, HuggingFace, Groq, Ollama, Custom
- Anthropic: covers Claude (different message format + auth header)
- Gemini: thin adapter for Google's generateContent API

System prompt is built from AGENT_GUIDE.md + live user context.
Chat history is ephemeral (not persisted).
"""
from __future__ import annotations

import json
import logging
from typing import AsyncGenerator

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.services.crypto import decrypt_value
from app.models.integration_config import IntegrationConfig

logger = logging.getLogger(__name__)
settings = get_settings()

# AI provider presets — base_url and api_format for each named provider
AI_PRESETS = {
    "openai": {"base_url": "https://api.openai.com/v1", "format": "openai", "default_model": "gpt-4o-mini"},
    "openrouter": {"base_url": "https://openrouter.ai/api/v1", "format": "openai", "default_model": "openai/gpt-4o-mini"},
    "huggingface": {"base_url": "https://router.huggingface.co/v1", "format": "openai", "default_model": "meta-llama/Llama-3.3-70B-Instruct"},
    "groq": {"base_url": "https://api.groq.com/openai/v1", "format": "openai", "default_model": "llama-3.3-70b-versatile"},
    "ollama": {"base_url": "http://host.docker.internal:11434/v1", "format": "openai", "default_model": "llama3.1"},
    "claude": {"base_url": "https://api.anthropic.com/v1", "format": "anthropic", "default_model": "claude-sonnet-4-6"},
    "gemini": {"base_url": "https://generativelanguage.googleapis.com/v1beta", "format": "gemini", "default_model": "gemini-2.0-flash"},
    "custom_ai": {"base_url": "", "format": "openai", "default_model": ""},
}

# System prompt template — {context} is replaced with live user data
SYSTEM_PROMPT_TEMPLATE = """You are a fitness coach integrated with Diligence, a self-hosted fitness rewards platform.

Your role: motivate, guide, and help the user stay consistent with their health goals. Use the context below to personalize your responses.

CURRENT USER CONTEXT:
{context}

RULES:
- Be encouraging but honest. Celebrate progress, address setbacks constructively.
- When the user asks to log a workout or food, confirm what you'll log and do it.
- Reference their program schedule when suggesting workouts.
- Respect their motivation type (from BREQ-2 profiling) to calibrate your tone.
- Keep responses concise — this is a mobile chat, not an essay.
- If the user hasn't earned enough points today, gently encourage activity.
- Never fabricate data — only reference what's in the context."""


async def get_active_ai_provider(db: AsyncSession) -> dict | None:
    """Find the first configured AI provider."""
    result = await db.execute(
        select(IntegrationConfig).where(
            IntegrationConfig.provider.in_(list(AI_PRESETS.keys()))
        )
    )
    configs = result.scalars().all()

    for config in configs:
        provider_name = config.provider
        try:
            creds = json.loads(decrypt_value(config.encrypted_value, settings.secret_key))
        except Exception:
            continue

        preset = AI_PRESETS.get(provider_name, AI_PRESETS["custom_ai"])
        api_key = creds.get("api_key", "")
        base_url = creds.get("endpoint_url", preset["base_url"]) or preset["base_url"]
        model = creds.get("model", preset["default_model"]) or preset["default_model"]

        return {
            "name": provider_name,
            "format": preset["format"],
            "base_url": base_url,
            "api_key": api_key,
            "model": model,
        }

    return None


async def build_context(db: AsyncSession, user_id) -> str:
    """Build live context string from user's current state."""
    from app.models.user import User
    from app.models.profile import UserProfile

    context_parts = []

    # User profile
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if user:
        context_parts.append(f"Name: {user.display_name}")
        context_parts.append(f"Timezone: {user.timezone}")

    # Profile / motivation
    profile = (await db.execute(select(UserProfile).where(UserProfile.user_id == user_id))).scalar_one_or_none()
    if profile:
        if profile.ttm_stage:
            context_parts.append(f"Stage of change: {profile.ttm_stage}")
        if profile.breq_profile:
            context_parts.append(f"Motivation type: {profile.breq_profile}")

    # Today's points (best effort)
    try:
        from app.services.points_engine import get_daily_summary
        summary = await get_daily_summary(db, user_id)
        context_parts.append(f"Today's points: {summary.get('earned', 0)}/{summary.get('target', 100)}")
        context_parts.append(f"Daily gate: {'PASSED' if summary.get('gate_passed') else 'NOT YET'}")
    except Exception:
        pass

    return "\n".join(context_parts) if context_parts else "No profile data available yet."


async def chat(
    user_id,
    message: str,
    history: list[dict],
    db: AsyncSession,
) -> AsyncGenerator[str, None]:
    """Route chat to the configured AI provider with streaming."""
    provider = await get_active_ai_provider(db)
    if not provider:
        yield "No AI provider configured. Go to Settings → Integrations to connect one (OpenAI, OpenRouter, Ollama, etc.)."
        return

    context = await build_context(db, user_id)
    system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context)

    try:
        if provider["format"] == "openai":
            async for chunk in _call_openai_compat(
                base_url=provider["base_url"],
                api_key=provider["api_key"],
                model=provider["model"],
                system_prompt=system_prompt,
                history=history,
                message=message,
            ):
                yield chunk
        elif provider["format"] == "anthropic":
            async for chunk in _call_anthropic(
                api_key=provider["api_key"],
                model=provider["model"],
                system_prompt=system_prompt,
                history=history,
                message=message,
            ):
                yield chunk
        elif provider["format"] == "gemini":
            async for chunk in _call_gemini(
                api_key=provider["api_key"],
                model=provider["model"],
                system_prompt=system_prompt,
                history=history,
                message=message,
            ):
                yield chunk
    except httpx.HTTPStatusError as e:
        yield f"AI provider error ({e.response.status_code}). Check your API key in Settings → Integrations."
    except httpx.ConnectError:
        yield f"Cannot reach {provider['name']}. Check your network or endpoint URL."
    except Exception as e:
        logger.error(f"AI chat error: {e}")
        yield "Something went wrong with the AI provider. Check Settings → Integrations."


async def _call_openai_compat(
    base_url: str,
    api_key: str,
    model: str,
    system_prompt: str,
    history: list[dict],
    message: str,
) -> AsyncGenerator[str, None]:
    """Call any OpenAI-compatible /v1/chat/completions endpoint with streaming.

    Covers: OpenAI, OpenRouter, HuggingFace, Groq, Ollama, Custom.
    """
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            *history,
            {"role": "user", "content": message},
        ],
        "stream": True,
        "max_tokens": 1024,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream(
            "POST",
            f"{base_url.rstrip('/')}/chat/completions",
            json=payload,
            headers=headers,
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: ") and line.strip() != "data: [DONE]":
                    try:
                        chunk = json.loads(line[6:])
                        delta = chunk.get("choices", [{}])[0].get("delta", {})
                        if content := delta.get("content"):
                            yield content
                    except (json.JSONDecodeError, IndexError, KeyError):
                        continue


async def _call_anthropic(
    api_key: str,
    model: str,
    system_prompt: str,
    history: list[dict],
    message: str,
) -> AsyncGenerator[str, None]:
    """Call Anthropic's /v1/messages endpoint with streaming."""
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
    }

    # Convert OpenAI-style history to Anthropic format
    messages = []
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})

    payload = {
        "model": model,
        "system": system_prompt,
        "messages": messages,
        "max_tokens": 1024,
        "stream": True,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream(
            "POST",
            "https://api.anthropic.com/v1/messages",
            json=payload,
            headers=headers,
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    try:
                        event = json.loads(line[6:])
                        if event.get("type") == "content_block_delta":
                            delta = event.get("delta", {})
                            if text := delta.get("text"):
                                yield text
                    except (json.JSONDecodeError, KeyError):
                        continue


async def _call_gemini(
    api_key: str,
    model: str,
    system_prompt: str,
    history: list[dict],
    message: str,
) -> AsyncGenerator[str, None]:
    """Call Google Gemini's generateContent endpoint with streaming."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:streamGenerateContent"

    # Build Gemini content format
    contents = []
    # System instruction goes as first user/model exchange
    if system_prompt:
        contents.append({"role": "user", "parts": [{"text": f"[System instructions]\n{system_prompt}"}]})
        contents.append({"role": "model", "parts": [{"text": "Understood. I'll follow these instructions."}]})

    for msg in history:
        role = "model" if msg["role"] == "assistant" else "user"
        contents.append({"role": role, "parts": [{"text": msg["content"]}]})
    contents.append({"role": "user", "parts": [{"text": message}]})

    payload = {
        "contents": contents,
        "generationConfig": {"maxOutputTokens": 1024},
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream(
            "POST",
            url,
            json=payload,
            params={"key": api_key, "alt": "sse"},
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    try:
                        chunk = json.loads(line[6:])
                        candidates = chunk.get("candidates", [])
                        if candidates:
                            parts = candidates[0].get("content", {}).get("parts", [])
                            for part in parts:
                                if text := part.get("text"):
                                    yield text
                    except (json.JSONDecodeError, KeyError):
                        continue
