from __future__ import annotations

from typing import Annotated
from datetime import datetime, timezone
import uuid as uuid_mod
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.oauth import OAuthToken
from app.utils.auth import get_current_user
from app.services.strava_sync import (
    get_strava_auth_url, exchange_strava_code, sync_strava_activities,
)
from app.services.polar_sync import (
    get_polar_auth_url, exchange_polar_code, register_polar_user, sync_polar_activities,
)

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


@router.get("")
async def integration_status(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(OAuthToken).where(OAuthToken.user_id == user.id))
    tokens = result.scalars().all()
    providers = {t.provider: {"connected": True, "athlete_id": t.athlete_id} for t in tokens}
    return {
        "strava": providers.get("strava", {"connected": False}),
        "polar": providers.get("polar", {"connected": False}),
    }


# --- Strava ---
@router.get("/strava/auth")
async def strava_auth(user: Annotated[User, Depends(get_current_user)]):
    from app.utils.auth import create_access_token
    from datetime import timedelta
    state_token = create_access_token(str(user.id), expires_delta=timedelta(minutes=10))
    return {"auth_url": get_strava_auth_url(state_token)}


@router.get("/strava/callback")
async def strava_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    from jose import JWTError, jwt as jose_jwt
    from app.config import get_settings
    _settings = get_settings()
    try:
        payload = jose_jwt.decode(state, _settings.secret_key, algorithms=[_settings.algorithm])
        user_id = uuid_mod.UUID(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    data = await exchange_strava_code(code)

    # Upsert token
    result = await db.execute(
        select(OAuthToken).where(OAuthToken.user_id == user_id, OAuthToken.provider == "strava")
    )
    token = result.scalar_one_or_none()
    if token:
        token.access_token = data["access_token"]
        token.refresh_token = data["refresh_token"]
        token.expires_at = datetime.fromtimestamp(data["expires_at"], tz=timezone.utc)
        token.athlete_id = str(data.get("athlete", {}).get("id", ""))
        token.updated_at = datetime.now(timezone.utc)
    else:
        token = OAuthToken(
            user_id=user_id,
            provider="strava",
            access_token=data["access_token"],
            refresh_token=data["refresh_token"],
            expires_at=datetime.fromtimestamp(data["expires_at"], tz=timezone.utc),
            athlete_id=str(data.get("athlete", {}).get("id", "")),
            scope=data.get("scope", ""),
        )
        db.add(token)
    await db.flush()

    from app.config import get_settings
    return RedirectResponse(url=f"{get_settings().base_url}/settings/integrations?strava=connected")


@router.post("/strava/sync")
async def strava_sync(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    imported = await sync_strava_activities(db, user.id)
    return {"imported": len(imported), "activities": imported}


# --- Polar ---
@router.get("/polar/auth")
async def polar_auth(user: Annotated[User, Depends(get_current_user)]):
    from app.utils.auth import create_access_token
    from datetime import timedelta
    state_token = create_access_token(str(user.id), expires_delta=timedelta(minutes=10))
    return {"auth_url": get_polar_auth_url(state_token)}


@router.get("/polar/callback")
async def polar_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    from jose import JWTError, jwt as jose_jwt
    from app.config import get_settings
    _settings = get_settings()
    try:
        payload = jose_jwt.decode(state, _settings.secret_key, algorithms=[_settings.algorithm])
        user_id = uuid_mod.UUID(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
    data = await exchange_polar_code(code)

    # Register user with Polar
    await register_polar_user(data["access_token"])

    result = await db.execute(
        select(OAuthToken).where(OAuthToken.user_id == user_id, OAuthToken.provider == "polar")
    )
    token = result.scalar_one_or_none()
    if token:
        token.access_token = data["access_token"]
        token.athlete_id = str(data.get("x_user_id", ""))
        token.updated_at = datetime.now(timezone.utc)
    else:
        token = OAuthToken(
            user_id=user_id,
            provider="polar",
            access_token=data["access_token"],
            athlete_id=str(data.get("x_user_id", "")),
        )
        db.add(token)
    await db.flush()

    from app.config import get_settings
    return RedirectResponse(url=f"{get_settings().base_url}/settings/integrations?polar=connected")


@router.post("/polar/sync")
async def polar_sync(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    imported = await sync_polar_activities(db, user.id)
    return {"imported": len(imported), "activities": imported}


# --- Disconnect ---
@router.delete("/{provider}")
async def disconnect(
    provider: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if provider not in ("strava", "polar"):
        raise HTTPException(status_code=400, detail="Invalid provider")
    result = await db.execute(
        select(OAuthToken).where(OAuthToken.user_id == user.id, OAuthToken.provider == provider)
    )
    token = result.scalar_one_or_none()
    if token:
        await db.delete(token)
    return {"status": "disconnected", "provider": provider}


# --- Dynamic Integration Config (v3) ---

from pydantic import BaseModel
from app.models.integration_config import IntegrationConfig
from app.services.provider_registry import PROVIDER_REGISTRY
from app.services.crypto import encrypt_value, decrypt_value
from app.config import settings


class ConfigureRequest(BaseModel):
    provider: str
    credentials: dict[str, str]


@router.get("/status")
async def full_integration_status(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Return connection status for all providers. Never returns actual credentials."""
    # OAuth tokens (Strava, Polar)
    oauth_result = await db.execute(select(OAuthToken).where(OAuthToken.user_id == user.id))
    oauth_tokens = {t.provider: True for t in oauth_result.scalars().all()}

    # Dynamic config entries
    config_result = await db.execute(
        select(IntegrationConfig.provider)
        .where(IntegrationConfig.user_id == user.id)
        .distinct()
    )
    configured_providers = {row[0] for row in config_result.all()}

    # Also check env vars for backward compatibility
    env_providers = set()
    if settings.strava_client_id:
        env_providers.add("strava")
    if settings.polar_client_id:
        env_providers.add("polar")
    if settings.telegram_bot_token:
        env_providers.add("telegram")
    if settings.groq_api_key:
        env_providers.add("groq")

    status = {}
    for key, info in PROVIDER_REGISTRY.items():
        if key in oauth_tokens:
            status[key] = "connected"
        elif key in configured_providers or key in env_providers:
            status[key] = "configured"
        else:
            status[key] = "not_configured"

    return status


@router.get("/providers")
async def list_providers():
    """Return the provider registry with setup instructions."""
    result = {}
    for key, info in PROVIDER_REGISTRY.items():
        result[key] = {
            "name": info["name"],
            "type": info["type"],
            "fields": info["fields"],
            "help_url": info.get("help_url", ""),
            "help_text": info.get("help_text", "").replace("{BASE_URL}", settings.base_url),
        }
    return result


@router.post("/configure")
async def configure_integration(
    body: ConfigureRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Store encrypted integration credentials. Write-only — values can never be read back."""
    if body.provider not in PROVIDER_REGISTRY:
        raise HTTPException(400, f"Unknown provider: {body.provider}")

    info = PROVIDER_REGISTRY[body.provider]
    expected_fields = set(info["fields"])
    provided_fields = set(body.credentials.keys())

    missing = expected_fields - provided_fields
    if missing:
        raise HTTPException(400, f"Missing required fields: {', '.join(missing)}")

    for key, value in body.credentials.items():
        encrypted = encrypt_value(settings.secret_key, value)

        # Upsert
        existing = await db.execute(
            select(IntegrationConfig).where(
                IntegrationConfig.user_id == user.id,
                IntegrationConfig.provider == body.provider,
                IntegrationConfig.config_key == key,
            )
        )
        row = existing.scalar_one_or_none()
        if row:
            row.config_value = encrypted
            row.updated_at = datetime.now(timezone.utc)
        else:
            db.add(IntegrationConfig(
                user_id=user.id,
                provider=body.provider,
                config_key=key,
                config_value=encrypted,
            ))

    return {"status": "configured", "provider": body.provider}
