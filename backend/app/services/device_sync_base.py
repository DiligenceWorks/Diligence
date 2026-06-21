"""Base class for device activity sync services.

All device sync implementations (garmin_sync, whoop_sync, oura_sync)
inherit from this class. The pattern mirrors the existing strava_sync
and polar_sync services but adds webhook support and a standard
interface for the generic webhook receiver endpoint.
"""
from __future__ import annotations

import abc
import uuid
import logging
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.oauth import OAuthToken
from app.models.integration_config import IntegrationConfig
from app.services.crypto import decrypt_value
from app.services.points_engine import log_activity_with_points

logger = logging.getLogger(__name__)
settings = get_settings()


class DeviceSyncBase(abc.ABC):
    """Abstract base for all device sync services.

    Subclasses implement the provider-specific OAuth flow, API calls,
    and data mapping. The base handles token storage/refresh patterns
    and the common activity logging pipeline.
    """

    PROVIDER: str  # e.g. "garmin", "whoop", "oura"
    API_BASE: str  # e.g. "https://apis.garmin.com"

    # ── OAuth ──

    @abc.abstractmethod
    async def get_auth_url(self, user_id: uuid.UUID, db: AsyncSession) -> str:
        """Generate the OAuth authorization URL for this provider."""

    @abc.abstractmethod
    async def handle_callback(
        self, code: str, state: str, db: AsyncSession
    ) -> dict:
        """Exchange authorization code for tokens, store them.

        Returns: {"success": True, "provider": "garmin"}
        """

    @abc.abstractmethod
    async def _refresh_token(self, token: OAuthToken, db: AsyncSession) -> OAuthToken:
        """Provider-specific token refresh logic."""

    # ── Sync ──

    @abc.abstractmethod
    async def sync_activities(
        self, user_id: uuid.UUID, db: AsyncSession
    ) -> list[dict]:
        """Pull new activities from the provider and award points.

        Returns list of imported activity dicts with points_earned.
        """

    # ── Webhooks ──

    @abc.abstractmethod
    async def validate_webhook(self, request_body: bytes, headers: dict) -> bool:
        """Validate an incoming webhook signature.

        Returns True if the webhook is authentic.
        """

    @abc.abstractmethod
    async def handle_webhook(
        self, payload: dict, db: AsyncSession
    ) -> dict:
        """Process an incoming webhook notification.

        Typically identifies the user and triggers sync_activities().
        Returns: {"processed": True, "activities_imported": N}
        """

    # ── Helpers (shared) ──

    async def get_valid_token(
        self, db: AsyncSession, user_id: uuid.UUID
    ) -> OAuthToken | None:
        """Get a valid OAuth token, refreshing if expired."""
        result = await db.execute(
            select(OAuthToken).where(
                OAuthToken.user_id == user_id,
                OAuthToken.provider == self.PROVIDER,
            )
        )
        token = result.scalar_one_or_none()
        if not token:
            return None

        if token.expires_at and token.expires_at < datetime.now(timezone.utc):
            try:
                token = await self._refresh_token(token, db)
            except Exception as e:
                logger.error(f"Token refresh failed for {self.PROVIDER}: {e}")
                return None

        return token

    async def get_credentials(self, db: AsyncSession) -> dict | None:
        """Get decrypted OAuth credentials from integration_configs."""
        import json
        result = await db.execute(
            select(IntegrationConfig).where(
                IntegrationConfig.provider == self.PROVIDER
            )
        )
        config = result.scalar_one_or_none()
        if not config:
            return None

        try:
            return json.loads(decrypt_value(config.encrypted_value, settings.secret_key))
        except Exception as e:
            logger.error(f"Failed to decrypt {self.PROVIDER} credentials: {e}")
            return None

    async def import_activity(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        *,
        title: str,
        category: str = "workout",
        activity_date: Any,
        duration_minutes: int | None = None,
        external_id: str | None = None,
        metadata: dict | None = None,
    ) -> dict:
        """Import a single activity using the standard points pipeline.

        Deduplicates by (user_id, provider, external_id).
        """
        from app.models.activity import ActivityLog

        if external_id:
            existing = await db.execute(
                select(ActivityLog).where(
                    ActivityLog.user_id == user_id,
                    ActivityLog.source == self.PROVIDER,
                    ActivityLog.external_id == external_id,
                )
            )
            if existing.scalar_one_or_none():
                return {"skipped": True, "external_id": external_id}

        entry = await log_activity_with_points(
            db=db,
            user_id=user_id,
            category=category,
            activity_date=activity_date,
            title=title,
            duration_minutes=duration_minutes,
            source=self.PROVIDER,
            external_id=external_id,
            metadata=metadata or {},
        )

        return {
            "id": str(entry.id),
            "title": entry.title,
            "points_earned": entry.points_earned,
            "activity_date": str(activity_date),
        }
