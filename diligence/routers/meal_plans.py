"""Meal plans router — CRUD, compliance tracking, progress."""
from __future__ import annotations

import uuid as uuid_mod
from datetime import date, datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from diligence.database import get_db
from diligence.models.user import User
from diligence.models.meal_plan import MealPlan, MealPlanItem, MealCompliance
from diligence.utils.auth import get_current_user

router = APIRouter(prefix="/api/meal-plans", tags=["meal-plans"])


# ── Schemas ──────────────────────────────────────────────────────────────

class MealItemCreate(BaseModel):
    day_number: int
    meal_type: str
    food_name: str
    description: str | None = None
    calories: int | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    fiber_g: float | None = None
    serving_size: str | None = None
    sort_order: int = 0


class MealPlanCreate(BaseModel):
    name: str
    diet_type: str | None = None
    daily_calories: int | None = None
    daily_protein_g: int | None = None
    daily_carbs_g: int | None = None
    daily_fat_g: int | None = None
    restrictions: list[str] = []
    duration_days: int
    start_date: date | None = None
    meals: list[MealItemCreate] = []


class ComplianceCreate(BaseModel):
    plan_item_id: str | None = None
    compliance_date: date | None = None
    status: str  # followed, substituted, skipped
    substitution: str | None = None


# ── Endpoints ────────────────────────────────────────────────────────────

@router.get("")
async def list_meal_plans(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(MealPlan)
        .where(MealPlan.user_id == user.id)
        .order_by(MealPlan.created_at.desc())
    )
    plans = result.scalars().all()
    return [_plan_summary(p) for p in plans]


@router.post("", status_code=201)
async def create_meal_plan(
    body: MealPlanCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Deactivate any existing active plan
    result = await db.execute(
        select(MealPlan)
        .where(MealPlan.user_id == user.id, MealPlan.status == "active")
    )
    for old in result.scalars().all():
        old.status = "completed"

    plan = MealPlan(
        user_id=user.id,
        name=body.name,
        diet_type=body.diet_type,
        daily_calories=body.daily_calories,
        daily_protein_g=body.daily_protein_g,
        daily_carbs_g=body.daily_carbs_g,
        daily_fat_g=body.daily_fat_g,
        restrictions=body.restrictions,
        duration_days=body.duration_days,
        start_date=body.start_date or date.today(),
    )
    db.add(plan)
    await db.flush()

    for item in body.meals:
        db.add(MealPlanItem(
            plan_id=plan.id,
            day_number=item.day_number,
            meal_type=item.meal_type,
            food_name=item.food_name,
            description=item.description,
            calories=item.calories,
            protein_g=item.protein_g,
            carbs_g=item.carbs_g,
            fat_g=item.fat_g,
            fiber_g=item.fiber_g,
            serving_size=item.serving_size,
            sort_order=item.sort_order,
        ))

    return {"id": str(plan.id), "name": plan.name, "items_count": len(body.meals)}


@router.get("/today")
async def get_today_meals(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(MealPlan)
        .where(MealPlan.user_id == user.id, MealPlan.status == "active")
    )
    plan = result.scalar_one_or_none()
    if not plan:
        return {"active_plan": None}

    day_num = (date.today() - plan.start_date).days + 1
    if day_num < 1 or day_num > plan.duration_days:
        return {"active_plan": plan.name, "day": day_num, "meals": [], "message": "No meals planned for today"}

    items_result = await db.execute(
        select(MealPlanItem)
        .where(MealPlanItem.plan_id == plan.id, MealPlanItem.day_number == day_num)
        .order_by(MealPlanItem.sort_order)
    )
    items = items_result.scalars().all()

    return {
        "active_plan": plan.name,
        "diet_type": plan.diet_type,
        "day": day_num,
        "duration_days": plan.duration_days,
        "daily_calories": plan.daily_calories,
        "meals": [
            {
                "id": str(i.id),
                "meal_type": i.meal_type,
                "food_name": i.food_name,
                "description": i.description,
                "calories": i.calories,
                "protein_g": float(i.protein_g) if i.protein_g else None,
                "carbs_g": float(i.carbs_g) if i.carbs_g else None,
                "fat_g": float(i.fat_g) if i.fat_g else None,
            }
            for i in items
        ],
    }


@router.get("/{plan_id}")
async def get_meal_plan(
    plan_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(MealPlan)
        .where(MealPlan.id == uuid_mod.UUID(plan_id), MealPlan.user_id == user.id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(404, "Plan not found")

    return {**_plan_summary(plan), "items": [_item_detail(i) for i in plan.items]}


@router.patch("/{plan_id}")
async def update_meal_plan_status(
    plan_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status: str = "completed",
):
    result = await db.execute(
        select(MealPlan)
        .where(MealPlan.id == uuid_mod.UUID(plan_id), MealPlan.user_id == user.id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(404, "Plan not found")
    plan.status = status
    return {"id": str(plan.id), "status": plan.status}


@router.post("/compliance", status_code=201)
async def log_compliance(
    body: ComplianceCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # Find active plan
    result = await db.execute(
        select(MealPlan).where(MealPlan.user_id == user.id, MealPlan.status == "active")
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(400, "No active meal plan")

    entry = MealCompliance(
        user_id=user.id,
        plan_id=plan.id,
        plan_item_id=uuid_mod.UUID(body.plan_item_id) if body.plan_item_id else None,
        compliance_date=body.compliance_date or date.today(),
        status=body.status,
        substitution=body.substitution,
    )
    db.add(entry)
    return {"status": body.status, "date": str(entry.compliance_date)}


@router.get("/{plan_id}/progress")
async def get_plan_progress(
    plan_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(MealPlan)
        .where(MealPlan.id == uuid_mod.UUID(plan_id), MealPlan.user_id == user.id)
    )
    plan = result.scalar_one_or_none()
    if not plan:
        raise HTTPException(404, "Plan not found")

    comp_result = await db.execute(
        select(MealCompliance)
        .where(MealCompliance.plan_id == plan.id, MealCompliance.user_id == user.id)
    )
    entries = comp_result.scalars().all()

    total = len(entries)
    followed = sum(1 for e in entries if e.status == "followed")
    substituted = sum(1 for e in entries if e.status == "substituted")
    skipped = sum(1 for e in entries if e.status == "skipped")

    days_elapsed = (date.today() - plan.start_date).days + 1
    compliance_pct = (followed + substituted) / total * 100 if total > 0 else 0

    return {
        "plan": plan.name,
        "days_elapsed": min(days_elapsed, plan.duration_days),
        "duration_days": plan.duration_days,
        "total_entries": total,
        "followed": followed,
        "substituted": substituted,
        "skipped": skipped,
        "compliance_pct": round(compliance_pct, 1),
    }


# ── Helpers ──────────────────────────────────────────────────────────────

def _plan_summary(p: MealPlan) -> dict:
    return {
        "id": str(p.id),
        "name": p.name,
        "diet_type": p.diet_type,
        "daily_calories": p.daily_calories,
        "duration_days": p.duration_days,
        "start_date": str(p.start_date),
        "status": p.status,
    }


def _item_detail(i: MealPlanItem) -> dict:
    return {
        "id": str(i.id),
        "day_number": i.day_number,
        "meal_type": i.meal_type,
        "food_name": i.food_name,
        "description": i.description,
        "calories": i.calories,
        "protein_g": float(i.protein_g) if i.protein_g else None,
        "carbs_g": float(i.carbs_g) if i.carbs_g else None,
        "fat_g": float(i.fat_g) if i.fat_g else None,
        "fiber_g": float(i.fiber_g) if i.fiber_g else None,
        "serving_size": i.serving_size,
    }
