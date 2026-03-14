"""Strava API client for activity sync."""
import uuid
from datetime import datetime, timezone
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.oauth import OAuthToken
from app.models.activity import ActivityLog
from app.services.points_engine import log_activity_with_points

settings = get_settings()

STRAVA_AUTH_URL = "https://www.strava.com/oauth/authorize"
STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
STRAVA_API = "https://www.strava.com/api/v3"

# Map Strava activity types to our categories
STRAVA_TYPE_MAP = {
    "Run": "workout",
    "Ride": "workout",
    "Swim": "workout",
    "Walk": "workout",
    "Hike": "workout",
    "WeightTraining": "workout",
    "Crossfit": "workout",
    "Yoga": "workout",
    "Workout": "workout",
}


def get_strava_auth_url(user_id: str) -> str:
    """Generate the Strava OAuth authorization URL."""
    return (
        f"{STRAVA_AUTH_URL}?client_id={settings.strava_client_id}"
        f"&response_type=code"
        f"&redirect_uri={settings.base_url}/api/integrations/strava/callback"
        f"&scope=read,activity:read_all"
        f"&approval_prompt=force"
        f"&state={user_id}"
    )


async def exchange_strava_code(code: str) -> dict:
    """Exchange authorization code for tokens."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(STRAVA_TOKEN_URL, data={
            "client_id": settings.strava_client_id,
            "client_secret": settings.strava_client_secret,
            "code": code,
            "grant_type": "authorization_code",
        })
        resp.raise_for_status()
        return resp.json()


async def refresh_strava_token(token: OAuthToken, db: AsyncSession) -> OAuthToken:
    """Refresh an expired Strava access token."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(STRAVA_TOKEN_URL, data={
            "client_id": settings.strava_client_id,
            "client_secret": settings.strava_client_secret,
            "refresh_token": token.refresh_token,
            "grant_type": "refresh_token",
        })
        resp.raise_for_status()
        data = resp.json()

    token.access_token = data["access_token"]
    token.refresh_token = data.get("refresh_token", token.refresh_token)
    token.expires_at = datetime.fromtimestamp(data["expires_at"], tz=timezone.utc)
    token.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return token


async def get_valid_token(db: AsyncSession, user_id: uuid.UUID) -> OAuthToken | None:
    """Get a valid Strava token, refreshing if needed."""
    result = await db.execute(
        select(OAuthToken).where(OAuthToken.user_id == user_id, OAuthToken.provider == "strava")
    )
    token = result.scalar_one_or_none()
    if not token:
        return None

    if token.expires_at and token.expires_at < datetime.now(timezone.utc):
        token = await refresh_strava_token(token, db)

    return token


async def sync_strava_activities(db: AsyncSession, user_id: uuid.UUID) -> list[dict]:
    """Pull new activities from Strava and award points."""
    token = await get_valid_token(db, user_id)
    if not token:
        return []

    # Find the most recent synced activity date to avoid duplicates
    result = await db.execute(
        select(ActivityLog.logged_at)
        .where(ActivityLog.user_id == user_id, ActivityLog.source == "strava")
        .order_by(ActivityLog.logged_at.desc())
        .limit(1)
    )
    last_sync = result.scalar_one_or_none()
    after_ts = int(last_sync.timestamp()) if last_sync else 0

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{STRAVA_API}/athlete/activities",
            params={"after": after_ts, "per_page": 30},
            headers={"Authorization": f"Bearer {token.access_token}"},
        )
        if resp.status_code != 200:
            return []
        activities = resp.json()

    imported = []
    for act in activities:
        ext_id = str(act["id"])

        # Skip if already imported
        existing = await db.execute(
            select(ActivityLog).where(
                ActivityLog.user_id == user_id,
                ActivityLog.source == "strava",
                ActivityLog.external_id == ext_id,
            )
        )
        if existing.scalar_one_or_none():
            continue

        category = STRAVA_TYPE_MAP.get(act.get("type", ""), "workout")
        start_local = act.get("start_date_local", act.get("start_date", ""))
        activity_date = datetime.fromisoformat(start_local.replace("Z", "+00:00")).date()

        entry = await log_activity_with_points(
            db=db,
            user_id=user_id,
            category=category,
            activity_date=activity_date,
            title=act.get("name", "Strava Activity"),
            duration_minutes=(act.get("elapsed_time", 0) // 60) or None,
            source="strava",
            external_id=ext_id,
            metadata={
                "distance_km": round(act.get("distance", 0) / 1000, 2),
                "calories": act.get("calories"),
                "average_heartrate": act.get("average_heartrate"),
                "type": act.get("type"),
                "moving_time": act.get("moving_time"),
            },
        )
        imported.append({
            "id": str(entry.id),
            "title": entry.title,
            "points_earned": entry.points_earned,
            "activity_date": activity_date.isoformat(),
        })

    return imported
