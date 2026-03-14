from datetime import date, datetime
from pydantic import BaseModel


class ActivityCreate(BaseModel):
    category: str  # workout, food_log, steps_target, screen_free, daily_checkin
    title: str | None = None
    description: str | None = None
    duration_minutes: int | None = None
    activity_date: date
    program_id: str | None = None
    program_day: int | None = None
    metadata: dict = {}


class ActivityResponse(BaseModel):
    id: str
    category: str
    title: str | None
    description: str | None
    duration_minutes: int | None
    source: str
    points_earned: int
    activity_date: date
    logged_at: datetime
    program_id: str | None
    program_day: int | None
    metadata_json: dict

    model_config = {"from_attributes": True}
