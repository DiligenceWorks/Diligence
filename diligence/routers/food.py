from __future__ import annotations

from typing import Annotated
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from diligence.database import get_db
from diligence.models.user import User
from diligence.models.food import FoodLog
from diligence.schemas.food import FoodCreate, FoodSearchResult
from diligence.utils.auth import get_current_user
from diligence.services.food_lookup import lookup_barcode, search_food

router = APIRouter(prefix="/api/food", tags=["food"])


@router.get("")
async def list_food(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    food_date: date | None = Query(None, alias="date"),
):
    query = select(FoodLog).where(FoodLog.user_id == user.id)
    if food_date:
        query = query.where(FoodLog.food_date == food_date)
    query = query.order_by(FoodLog.logged_at.desc()).limit(100)
    result = await db.execute(query)
    items = result.scalars().all()

    # Group by meal type
    meals = {"breakfast": [], "lunch": [], "dinner": [], "snack": []}
    total_cals = 0
    for item in items:
        entry = {
            "id": str(item.id),
            "food_name": item.food_name,
            "brand": item.brand,
            "serving_size": item.serving_size,
            "servings": float(item.servings) if item.servings else 1,
            "calories": float(item.calories) if item.calories else None,
            "protein_g": float(item.protein_g) if item.protein_g else None,
            "carbs_g": float(item.carbs_g) if item.carbs_g else None,
            "fat_g": float(item.fat_g) if item.fat_g else None,
        }
        meals.get(item.meal_type, meals["snack"]).append(entry)
        if item.calories:
            total_cals += float(item.calories) * float(item.servings or 1)

    return {"date": (food_date or date.today()).isoformat(), "meals": meals, "total_calories": round(total_cals, 1)}


@router.post("")
async def log_food(
    req: FoodCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    entry = FoodLog(
        user_id=user.id,
        meal_type=req.meal_type,
        food_name=req.food_name,
        brand=req.brand,
        barcode=req.barcode,
        serving_size=req.serving_size,
        servings=Decimal(str(req.servings)),
        calories=Decimal(str(req.calories)) if req.calories else None,
        protein_g=Decimal(str(req.protein_g)) if req.protein_g else None,
        carbs_g=Decimal(str(req.carbs_g)) if req.carbs_g else None,
        fat_g=Decimal(str(req.fat_g)) if req.fat_g else None,
        fiber_g=Decimal(str(req.fiber_g)) if req.fiber_g else None,
        sodium_mg=Decimal(str(req.sodium_mg)) if req.sodium_mg else None,
        sugar_g=Decimal(str(req.sugar_g)) if req.sugar_g else None,
        food_date=req.food_date,
        off_product_id=req.off_product_id,
        off_data=req.off_data,
    )
    db.add(entry)
    await db.flush()
    return {"id": str(entry.id), "food_name": entry.food_name, "calories": float(entry.calories) if entry.calories else None}


@router.delete("/{food_id}")
async def delete_food(
    food_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    import uuid
    result = await db.execute(
        select(FoodLog).where(FoodLog.id == uuid.UUID(food_id), FoodLog.user_id == user.id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise HTTPException(status_code=404, detail="Food entry not found")
    await db.delete(entry)
    return {"status": "deleted"}


@router.get("/scan/{barcode}")
async def scan_barcode(barcode: str):
    result = await lookup_barcode(barcode)
    if not result:
        raise HTTPException(status_code=404, detail="Product not found in Open Food Facts")
    return result


@router.get("/search")
async def food_search(q: str = Query(..., min_length=2)):
    results = await search_food(q)
    return {"results": results}
