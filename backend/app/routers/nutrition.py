from __future__ import annotations

"""Nutrition router — goals, fasts, electrolytes, daily compliance."""

import uuid
from typing import Annotated
from datetime import datetime, date, timezone, timedelta
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.nutrition import NutritionGoal, Fast, ElectrolyteLog
from app.models.food import FoodLog
from app.schemas.nutrition import (
    NutritionGoalIn, NutritionGoalOut, FastStart, FastUpdate, FastOut, ElectrolyteIn,
)
from app.utils.auth import get_current_user
from app.services.points_engine import log_activity_with_points

router = APIRouter(prefix="/api/nutrition", tags=["nutrition"])


# ---------- Goals ----------

async def _get_or_create_goal(db: AsyncSession, user_id: uuid.UUID) -> NutritionGoal:
    result = await db.execute(select(NutritionGoal).where(NutritionGoal.user_id == user_id))
    goal = result.scalar_one_or_none()
    if goal:
        return goal
    goal = NutritionGoal(user_id=user_id)
    db.add(goal)
    await db.flush()
    return goal


def _goal_to_out(g: NutritionGoal) -> dict:
    return {
        "id": str(g.id),
        "calorie_target": g.calorie_target,
        "protein_g_target": g.protein_g_target,
        "fat_g_target": g.fat_g_target,
        "net_carbs_g_cap": g.net_carbs_g_cap,
        "training_calorie_target": g.training_calorie_target,
        "training_protein_g_target": g.training_protein_g_target,
        "training_fat_g_target": g.training_fat_g_target,
        "eating_window_start_hour": g.eating_window_start_hour,
        "eating_window_end_hour": g.eating_window_end_hour,
        "default_fast_hours": g.default_fast_hours,
        "diet_style": g.diet_style,
        "timezone_str": g.timezone_str,
    }


@router.get("/goals")
async def get_goals(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    goal = await _get_or_create_goal(db, user.id)
    return _goal_to_out(goal)


@router.patch("/goals")
async def update_goals(
    req: NutritionGoalIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    goal = await _get_or_create_goal(db, user.id)
    for k, v in req.model_dump(exclude_unset=True).items():
        if v is not None:
            setattr(goal, k, v)
    goal.updated_at = datetime.now(timezone.utc)
    await db.flush()
    return _goal_to_out(goal)


# ---------- Today's macro status ----------

@router.get("/today")
async def get_today(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Today's macros vs target, eating-window state, active fast, compliance."""
    goal = await _get_or_create_goal(db, user.id)
    today = date.today()

    # Sum today's food
    result = await db.execute(
        select(
            func.coalesce(func.sum(FoodLog.calories * FoodLog.servings), 0),
            func.coalesce(func.sum(FoodLog.protein_g * FoodLog.servings), 0),
            func.coalesce(func.sum(FoodLog.carbs_g * FoodLog.servings), 0),
            func.coalesce(func.sum(FoodLog.fat_g * FoodLog.servings), 0),
            func.coalesce(func.sum(FoodLog.fiber_g * FoodLog.servings), 0),
        ).where(FoodLog.user_id == user.id, FoodLog.food_date == today)
    )
    cals, prot, carbs, fat, fiber = result.one()
    cals, prot, carbs, fat, fiber = float(cals), float(prot), float(carbs), float(fat), float(fiber)
    net_carbs = max(0.0, carbs - fiber)

    # Eating window (local time, using goal timezone_str — simplified: assume server in UTC, user sends local)
    now_local = datetime.now(timezone.utc) + timedelta(hours=7)  # Asia/Bangkok offset hack
    hour = now_local.hour
    in_window = goal.eating_window_start_hour <= hour < goal.eating_window_end_hour
    window_str = f"{goal.eating_window_start_hour:02d}:00–{goal.eating_window_end_hour:02d}:00"

    # Active fast
    result = await db.execute(
        select(Fast).where(Fast.user_id == user.id, Fast.ended_at.is_(None))
        .order_by(Fast.started_at.desc()).limit(1)
    )
    active_fast = result.scalar_one_or_none()
    active_fast_data = None
    if active_fast:
        elapsed = (datetime.now(timezone.utc) - active_fast.started_at).total_seconds() / 3600
        active_fast_data = {
            "id": str(active_fast.id),
            "started_at": active_fast.started_at.isoformat(),
            "target_hours": active_fast.target_hours,
            "fast_type": active_fast.fast_type,
            "elapsed_hours": round(elapsed, 2),
            "target_reached": elapsed >= active_fast.target_hours,
        }

    # Compliance for today
    carb_ok = net_carbs <= goal.net_carbs_g_cap
    protein_ok = prot >= goal.protein_g_target * 0.85  # 85% threshold gives some slack
    compliant_day = carb_ok and protein_ok

    return {
        "date": today.isoformat(),
        "macros": {
            "calories": round(cals, 0),
            "protein_g": round(prot, 1),
            "carbs_g": round(carbs, 1),
            "net_carbs_g": round(net_carbs, 1),
            "fat_g": round(fat, 1),
            "fiber_g": round(fiber, 1),
        },
        "targets": {
            "calories": goal.calorie_target,
            "protein_g": goal.protein_g_target,
            "fat_g": goal.fat_g_target,
            "net_carbs_cap": goal.net_carbs_g_cap,
        },
        "compliance": {
            "carb_ok": carb_ok,
            "protein_ok": protein_ok,
            "compliant_day": compliant_day,
        },
        "eating_window": {
            "start": goal.eating_window_start_hour,
            "end": goal.eating_window_end_hour,
            "display": window_str,
            "in_window_now": in_window,
        },
        "active_fast": active_fast_data,
    }


# ---------- Fasts ----------

def _fast_to_out(f: Fast) -> dict:
    if f.ended_at:
        elapsed = (f.ended_at - f.started_at).total_seconds() / 3600
    else:
        elapsed = (datetime.now(timezone.utc) - f.started_at).total_seconds() / 3600
    return {
        "id": str(f.id),
        "started_at": f.started_at.isoformat(),
        "ended_at": f.ended_at.isoformat() if f.ended_at else None,
        "target_hours": f.target_hours,
        "fast_type": f.fast_type,
        "completed": f.completed,
        "broken_early": f.broken_early,
        "points_awarded": f.points_awarded,
        "elapsed_hours": round(elapsed, 2),
        "notes": f.notes,
    }


# Points schedule per design doc
FAST_POINTS = {
    16: 25,   # 16:8 daily
    18: 40,   # 18:6
    20: 60,   # 20:4
    24: 200,  # 24h weekly
    36: 350,
    48: 500,  # 48h monthly
    72: 1000, # 72h kickoff
}


def _points_for_fast(target_hours: int, elapsed_hours: float) -> int:
    """Award the highest tier the user actually reached, capped at target."""
    # Find the highest tier <= min(target, elapsed)
    achieved = min(target_hours, int(elapsed_hours))
    best = 0
    for tier, pts in FAST_POINTS.items():
        if tier <= achieved and pts > best:
            best = pts
    return best


@router.post("/fasts")
async def start_fast(
    req: FastStart,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Reject if there's already an active fast
    result = await db.execute(
        select(Fast).where(Fast.user_id == user.id, Fast.ended_at.is_(None))
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="An active fast already exists — end it first")

    f = Fast(
        user_id=user.id,
        started_at=req.started_at or datetime.now(timezone.utc),
        target_hours=req.target_hours,
        fast_type=req.fast_type,
        notes=req.notes,
    )
    db.add(f)
    await db.flush()
    return _fast_to_out(f)


@router.get("/fasts")
async def list_fasts(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(20, le=100),
):
    result = await db.execute(
        select(Fast).where(Fast.user_id == user.id)
        .order_by(Fast.started_at.desc()).limit(limit)
    )
    return [_fast_to_out(f) for f in result.scalars().all()]


@router.get("/fasts/active")
async def get_active_fast(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Fast).where(Fast.user_id == user.id, Fast.ended_at.is_(None))
        .order_by(Fast.started_at.desc()).limit(1)
    )
    f = result.scalar_one_or_none()
    if not f:
        return {"active": False}
    return {"active": True, **_fast_to_out(f)}


@router.patch("/fasts/{fast_id}")
async def end_fast(
    fast_id: str,
    req: FastUpdate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Fast).where(Fast.id == uuid.UUID(fast_id), Fast.user_id == user.id)
    )
    f = result.scalar_one_or_none()
    if not f:
        raise HTTPException(status_code=404, detail="Fast not found")
    if f.ended_at:
        raise HTTPException(status_code=400, detail="Fast already ended")

    ended = req.ended_at or datetime.now(timezone.utc)
    if ended < f.started_at:
        raise HTTPException(status_code=400, detail="End time cannot be before start time")

    f.ended_at = ended
    if req.notes is not None:
        f.notes = req.notes

    elapsed_hours = (ended - f.started_at).total_seconds() / 3600
    f.completed = elapsed_hours >= f.target_hours
    f.broken_early = not f.completed

    # Award points for whatever tier was achieved (partial credit)
    pts = _points_for_fast(f.target_hours, elapsed_hours)
    if pts > 0 and f.points_awarded == 0:
        activity = await log_activity_with_points(
            db=db,
            user_id=user.id,
            category="fast_completed",
            activity_date=ended.date(),
            title=f"{f.fast_type} fast — {int(elapsed_hours)}h",
            duration_minutes=int(elapsed_hours * 60),
            source="nutrition",
            metadata={"fast_id": str(f.id), "target_hours": f.target_hours, "elapsed_hours": elapsed_hours},
        )
        # Override points with our tier-based calc (log_activity used default rule)
        activity.points_earned = pts
        f.activity_log_id = activity.id
        f.points_awarded = pts

    await db.flush()
    return _fast_to_out(f)


@router.delete("/fasts/{fast_id}")
async def delete_fast(
    fast_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(Fast).where(Fast.id == uuid.UUID(fast_id), Fast.user_id == user.id)
    )
    f = result.scalar_one_or_none()
    if not f:
        raise HTTPException(status_code=404, detail="Fast not found")
    await db.delete(f)
    return {"status": "deleted"}


# ---------- Electrolytes ----------

@router.post("/electrolytes")
async def log_electrolytes(
    req: ElectrolyteIn,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    entry = ElectrolyteLog(
        user_id=user.id,
        log_date=datetime.now(timezone.utc),
        sodium_mg=req.sodium_mg,
        potassium_mg=req.potassium_mg,
        magnesium_mg=req.magnesium_mg,
        notes=req.notes,
    )
    db.add(entry)
    await db.flush()
    return {"id": str(entry.id), "status": "logged"}


@router.get("/electrolytes/today")
async def get_electrolytes_today(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    today_start = datetime.combine(date.today(), datetime.min.time()).replace(tzinfo=timezone.utc)
    result = await db.execute(
        select(
            func.coalesce(func.sum(ElectrolyteLog.sodium_mg), 0),
            func.coalesce(func.sum(ElectrolyteLog.potassium_mg), 0),
            func.coalesce(func.sum(ElectrolyteLog.magnesium_mg), 0),
        ).where(
            ElectrolyteLog.user_id == user.id,
            ElectrolyteLog.log_date >= today_start,
        )
    )
    sodium, potassium, magnesium = result.one()
    return {
        "sodium_mg": int(sodium),
        "potassium_mg": int(potassium),
        "magnesium_mg": int(magnesium),
        "targets": {"sodium_mg": 5000, "potassium_mg": 3500, "magnesium_mg": 400},
    }
