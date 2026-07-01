from __future__ import annotations

"""Polar AccessLink API client for activity sync."""
import uuid
from datetime import datetime, timezone
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from diligence.config import get_settings
from diligence.models.oauth import OAuthToken
from diligence.models.activity import ActivityLog
from diligence.services.points_engine import log_activity_with_points

settings = get_settings()

POLAR_AUTH_URL = "https://flow.polar.com/oauth2/authorization"
POLAR_TOKEN_URL = "https://polarremote.com/v2/oauth2/token"
POLAR_API = "https://www.polaraccesslink.com/v3"


def get_polar_auth_url(user_id: str) -> str:
    return (
        f"{POLAR_AUTH_URL}?response_type=code"
        f"&client_id={settings.polar_client_id}"
        f"&redirect_uri={settings.base_url}/api/integrations/polar/callback"
        f"&state={user_id}"
    )


async def exchange_polar_code(code: str) -> dict:
    import base64
    creds = base64.b64encode(f"{settings.polar_client_id}:{settings.polar_client_secret}".encode()).decode()
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(POLAR_TOKEN_URL, data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": f"{settings.base_url}/api/integrations/polar/callback",
        }, headers={
            "Authorization": f"Basic {creds}",
            "Content-Type": "application/x-www-form-urlencoded",
        })
        resp.raise_for_status()
        return resp.json()


async def register_polar_user(access_token: str) -> dict | None:
    """Register user with Polar AccessLink (required before pulling data)."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{POLAR_API}/users",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json={"member-id": "fitness-rewards-user"},
        )
        if resp.status_code in (200, 409):  # 409 = already registered
            return resp.json() if resp.status_code == 200 else {"status": "already_registered"}
        return None


async def sync_polar_activities(db: AsyncSession, user_id: uuid.UUID) -> list[dict]:
    """Pull exercises from Polar AccessLink."""
    result = await db.execute(
        select(OAuthToken).where(OAuthToken.user_id == user_id, OAuthToken.provider == "polar")
    )
    token = result.scalar_one_or_none()
    if not token:
        return []

    headers = {"Authorization": f"Bearer {token.access_token}", "Accept": "application/json"}

    # List available exercises (transactional endpoint)
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f"{POLAR_API}/users/exercise-transactions", headers=headers)
        if resp.status_code != 200:
            return []
        tx_data = resp.json()

    imported = []
    for tx in tx_data.get("exercise-transactions", []):
        tx_url = tx.get("resource-uri", "")
        if not tx_url:
            continue

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(tx_url, headers=headers)
            if resp.status_code != 200:
                continue
            exercises = resp.json().get("exercises", [])

        for ex in exercises:
            ext_id = str(ex.get("id", ""))
            if not ext_id:
                continue

            # Skip duplicates
            existing = await db.execute(
                select(ActivityLog).where(
                    ActivityLog.user_id == user_id,
                    ActivityLog.source == "polar",
                    ActivityLog.external_id == ext_id,
                )
            )
            if existing.scalar_one_or_none():
                continue

            start = ex.get("start-time", "")
            try:
                activity_date = datetime.fromisoformat(start).date()
            except (ValueError, TypeError):
                from datetime import date
                activity_date = date.today()

            # Parse duration ISO 8601 (e.g., PT1H30M)
            duration_str = ex.get("duration", "")
            duration_min = None
            if duration_str:
                import re
                match = re.match(r"PT(?:(\d+)H)?(?:(\d+)M)?", duration_str)
                if match:
                    hours = int(match.group(1) or 0)
                    mins = int(match.group(2) or 0)
                    duration_min = hours * 60 + mins

            entry = await log_activity_with_points(
                db=db,
                user_id=user_id,
                category="workout",
                activity_date=activity_date,
                title=ex.get("sport", "Polar Exercise"),
                duration_minutes=duration_min,
                source="polar",
                external_id=ext_id,
                metadata={
                    "calories": ex.get("calories"),
                    "heart_rate_avg": ex.get("heart-rate", {}).get("average"),
                    "sport": ex.get("sport"),
                    "distance": ex.get("distance"),
                },
            )
            imported.append({
                "id": str(entry.id),
                "title": entry.title,
                "points_earned": entry.points_earned,
                "activity_date": activity_date.isoformat(),
            })

    return imported
