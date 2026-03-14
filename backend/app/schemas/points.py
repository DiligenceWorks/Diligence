from datetime import date
from pydantic import BaseModel


class PointRuleResponse(BaseModel):
    id: str
    category: str
    description: str
    points: int
    unit: str | None
    is_active: bool

    model_config = {"from_attributes": True}


class PointRuleUpdate(BaseModel):
    points: int | None = None
    description: str | None = None
    is_active: bool | None = None


class DailyTargetResponse(BaseModel):
    daily_minimum_pts: int
    weekly_target_pts: int
    weekly_bonus_pts: int

    model_config = {"from_attributes": True}


class DailyTargetUpdate(BaseModel):
    daily_minimum_pts: int | None = None
    weekly_target_pts: int | None = None
    weekly_bonus_pts: int | None = None


class DailySummary(BaseModel):
    date: date
    points_earned: int
    points_spent: int
    gate_passed: bool
    daily_minimum: int
    activities: list[dict] = []


class WeeklySummary(BaseModel):
    week_start: date
    week_end: date
    total_points_earned: int
    total_points_spent: int
    active_days: int
    gate_passed_days: int
    hit_weekly_target: bool
    weekly_target: int
    weekly_bonus_earned: int
    daily_breakdown: list[DailySummary] = []


class TodayStatus(BaseModel):
    date: date
    points_earned: int
    daily_minimum: int
    gate_passed: bool
    points_remaining: int
    activities_today: list[dict] = []
    rewards_available: list[dict] = []
    week_points: int
    weekly_target: int
    program_day: int | None = None
    program_total_days: int | None = None
