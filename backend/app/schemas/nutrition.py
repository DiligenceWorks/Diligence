from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class NutritionGoalIn(BaseModel):
    calorie_target: int | None = None
    protein_g_target: int | None = None
    fat_g_target: int | None = None
    net_carbs_g_cap: int | None = None
    training_calorie_target: int | None = None
    training_protein_g_target: int | None = None
    training_fat_g_target: int | None = None
    eating_window_start_hour: int | None = None
    eating_window_end_hour: int | None = None
    default_fast_hours: int | None = None
    diet_style: str | None = None
    timezone_str: str | None = None


class NutritionGoalOut(BaseModel):
    id: str
    calorie_target: int
    protein_g_target: int
    fat_g_target: int
    net_carbs_g_cap: int
    training_calorie_target: int | None
    training_protein_g_target: int | None
    training_fat_g_target: int | None
    eating_window_start_hour: int
    eating_window_end_hour: int
    default_fast_hours: int
    diet_style: str
    timezone_str: str


class FastStart(BaseModel):
    target_hours: int
    fast_type: str = "daily"          # daily, weekly_24, long_48, long_72, extended
    started_at: datetime | None = None  # defaults to now if omitted
    notes: str | None = None


class FastUpdate(BaseModel):
    ended_at: datetime | None = None  # defaults to now if omitted, terminates the fast
    notes: str | None = None


class FastOut(BaseModel):
    id: str
    started_at: datetime
    ended_at: datetime | None
    target_hours: int
    fast_type: str
    completed: bool
    broken_early: bool
    points_awarded: int
    elapsed_hours: float
    notes: str | None


class ElectrolyteIn(BaseModel):
    sodium_mg: int = 0
    potassium_mg: int = 0
    magnesium_mg: int = 0
    notes: str | None = None
