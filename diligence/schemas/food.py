from __future__ import annotations

from datetime import date, datetime
from pydantic import BaseModel


class FoodCreate(BaseModel):
    meal_type: str  # breakfast, lunch, dinner, snack
    food_name: str
    brand: str | None = None
    barcode: str | None = None
    serving_size: str | None = None
    servings: float = 1.0
    calories: float | None = None
    protein_g: float | None = None
    carbs_g: float | None = None
    fat_g: float | None = None
    fiber_g: float | None = None
    sodium_mg: float | None = None
    sugar_g: float | None = None
    food_date: date
    off_product_id: str | None = None
    off_data: dict = {}


class FoodResponse(BaseModel):
    id: str
    meal_type: str
    food_name: str
    brand: str | None
    barcode: str | None
    serving_size: str | None
    servings: float
    calories: float | None
    protein_g: float | None
    carbs_g: float | None
    fat_g: float | None
    food_date: date
    logged_at: datetime

    model_config = {"from_attributes": True}


class FoodSearchResult(BaseModel):
    barcode: str | None = None
    product_name: str | None = None
    brand: str | None = None
    calories_100g: float | None = None
    protein_100g: float | None = None
    carbs_100g: float | None = None
    fat_100g: float | None = None
    fiber_100g: float | None = None
    sugar_100g: float | None = None
    serving_size: str | None = None
    image_url: str | None = None
