from typing import Annotated
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.activity import ActivityLog
from app.schemas.activity import ActivityCreate, ActivityResponse
from app.utils.auth import get_current_user
from app.services.points_engine import log_activity_with_points

router = APIRouter(prefix="/api/activities", tags=["activities"])


@router.get("")
async def list_activities(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    activity_date: date | None = Query(None, alias="date"),
):
    query = select(ActivityLog).where(ActivityLog.user_id == user.id)
    if activity_date:
        query = query.where(ActivityLog.activity_date == activity_date)
    query = query.order_by(ActivityLog.logged_at.desc()).limit(50)
    result = await db.execute(query)
    activities = result.scalars().all()
    return [
        {
            "id": str(a.id),
            "category": a.category,
            "title": a.title,
            "description": a.description,
            "duration_minutes": a.duration_minutes,
            "source": a.source,
            "points_earned": a.points_earned,
            "activity_date": a.activity_date.isoformat(),
            "logged_at": a.logged_at.isoformat() if a.logged_at else None,
            "program_day": a.program_day,
            "metadata": a.metadata_json,
        }
        for a in activities
    ]


@router.post("")
async def create_activity(
    req: ActivityCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    import uuid as uuid_mod
    program_id = uuid_mod.UUID(req.program_id) if req.program_id else None

    entry = await log_activity_with_points(
        db=db,
        user_id=user.id,
        category=req.category,
        activity_date=req.activity_date,
        title=req.title,
        description=req.description,
        duration_minutes=req.duration_minutes,
        program_id=program_id,
        program_day=req.program_day,
        metadata=req.metadata,
    )
    return {
        "id": str(entry.id),
        "category": entry.category,
        "title": entry.title,
        "points_earned": entry.points_earned,
        "activity_date": entry.activity_date.isoformat(),
    }


@router.delete("/{activity_id}")
async def delete_activity(
    activity_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    import uuid as uuid_mod
    aid = uuid_mod.UUID(activity_id)
    result = await db.execute(
        select(ActivityLog).where(ActivityLog.id == aid, ActivityLog.user_id == user.id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Activity not found")
    await db.delete(entry)
    return {"status": "deleted"}
