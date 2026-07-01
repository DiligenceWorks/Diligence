from __future__ import annotations

from pydantic import BaseModel


class Phase1Request(BaseModel):
    primary_goal: str  # lose_weight, build_strength, get_active, feel_better
    ttm_stage: str  # precontemplation, contemplation, preparation, action, maintenance


class Phase2Request(BaseModel):
    # Body metrics (optional)
    age: int | None = None
    height_cm: float | None = None
    weight_kg: float | None = None
    gender: str | None = None

    # PAR-Q+
    parq_heart_condition: bool = False
    parq_joint_issues: bool = False
    parq_medications: bool = False
    parq_other_conditions: str | None = None

    # BREQ-2 motivation (1-5 scale)
    motivation_external: float | None = None
    motivation_introjected: float | None = None
    motivation_identified: float | None = None
    motivation_intrinsic: float | None = None
    motivation_amotivation: float | None = None

    # Preferences
    activity_preferences: list[str] = []
    equipment_access: str | None = None  # legacy single value
    equipment_list: list[str] = []  # new: list of equipment tags
    days_per_week: int = 3
    minutes_per_session: int = 30


class OnboardingStatusResponse(BaseModel):
    phase1_completed: bool
    phase2_completed: bool
    primary_goal: str | None = None
    ttm_stage: str | None = None

    model_config = {"from_attributes": True}
