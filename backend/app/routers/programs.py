from __future__ import annotations

from typing import Annotated
from datetime import date, timedelta
import uuid as uuid_mod
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.program import Program
from app.models.activity import ActivityLog
from app.utils.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/api/programs", tags=["programs"])


class ProgramCreate(BaseModel):
    name: str
    source: str | None = None
    source_url: str | None = None
    start_date: date
    duration_days: int = 90
    notes: str | None = None


@router.get("")
async def list_programs(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Program).where(Program.user_id == user.id).order_by(Program.created_at.desc())
    )
    programs = result.scalars().all()
    out = []
    for p in programs:
        today = date.today()
        day_num = (today - p.start_date).days + 1
        total = (p.end_date - p.start_date).days + 1
        out.append({
            "id": str(p.id), "name": p.name, "source": p.source, "source_url": p.source_url,
            "start_date": p.start_date.isoformat(), "end_date": p.end_date.isoformat(),
            "status": p.status, "current_day": min(day_num, total), "total_days": total,
        })
    return out


@router.post("")
async def create_program(
    req: ProgramCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    program = Program(
        user_id=user.id,
        name=req.name,
        source=req.source,
        source_url=req.source_url,
        start_date=req.start_date,
        end_date=req.start_date + timedelta(days=req.duration_days - 1),
        notes=req.notes,
    )
    db.add(program)
    await db.flush()
    return {"id": str(program.id), "name": program.name, "start_date": program.start_date.isoformat(), "end_date": program.end_date.isoformat()}


@router.get("/{program_id}")
async def get_program(
    program_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Program).where(Program.id == uuid_mod.UUID(program_id), Program.user_id == user.id)
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404)

    # Count logged days
    days_logged = await db.execute(
        select(func.count(func.distinct(ActivityLog.activity_date)))
        .where(ActivityLog.program_id == p.id)
    )
    logged = days_logged.scalar() or 0

    today = date.today()
    day_num = (today - p.start_date).days + 1
    total = (p.end_date - p.start_date).days + 1

    return {
        "id": str(p.id), "name": p.name, "source": p.source, "source_url": p.source_url,
        "start_date": p.start_date.isoformat(), "end_date": p.end_date.isoformat(),
        "status": p.status, "current_day": min(day_num, total), "total_days": total,
        "days_logged": logged, "notes": p.notes,
    }


@router.patch("/{program_id}")
async def update_program_status(
    program_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status: str = "completed",
):
    result = await db.execute(
        select(Program).where(Program.id == uuid_mod.UUID(program_id), Program.user_id == user.id)
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404)
    p.status = status
    await db.flush()
    return {"status": p.status}
