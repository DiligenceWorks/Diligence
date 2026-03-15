from __future__ import annotations

from typing import Annotated
from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.profile import UserProfile
from app.models.points import DailyTarget, TTM_DAILY_TARGETS
from app.schemas.onboarding import Phase1Request, Phase2Request, OnboardingStatusResponse
from app.utils.auth import get_current_user
from app.services.resource_matcher import get_recommendations

router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])


@router.get("/status", response_model=OnboardingStatusResponse)
async def onboarding_status(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        return OnboardingStatusResponse(phase1_completed=False, phase2_completed=False)
    return OnboardingStatusResponse(
        phase1_completed=profile.phase1_completed,
        phase2_completed=profile.phase2_completed,
        primary_goal=profile.primary_goal,
        ttm_stage=profile.ttm_stage,
    )


@router.post("/phase1")
async def save_phase1(
    req: Phase1Request,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)

    profile.primary_goal = req.primary_goal
    profile.ttm_stage = req.ttm_stage
    profile.phase1_completed = True

    # Adjust daily targets based on TTM stage
    targets = TTM_DAILY_TARGETS.get(req.ttm_stage, {})
    if targets:
        dt_result = await db.execute(select(DailyTarget).where(DailyTarget.user_id == user.id))
        dt = dt_result.scalar_one_or_none()
        if dt:
            dt.daily_minimum_pts = targets.get("daily_minimum_pts", dt.daily_minimum_pts)
            dt.weekly_target_pts = targets.get("weekly_target_pts", dt.weekly_target_pts)

    await db.flush()
    return {"status": "ok", "phase1_completed": True}


@router.post("/phase2")
async def save_phase2(
    req: Phase2Request,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(UserProfile).where(UserProfile.user_id == user.id))
    profile = result.scalar_one_or_none()
    if not profile:
        profile = UserProfile(user_id=user.id)
        db.add(profile)

    # Body metrics
    profile.age = req.age
    if req.height_cm is not None:
        profile.height_cm = Decimal(str(req.height_cm))
    if req.weight_kg is not None:
        profile.weight_kg = Decimal(str(req.weight_kg))
    profile.gender = req.gender

    # PAR-Q+
    profile.parq_heart_condition = req.parq_heart_condition
    profile.parq_joint_issues = req.parq_joint_issues
    profile.parq_medications = req.parq_medications
    profile.parq_other_conditions = req.parq_other_conditions
    profile.parq_cleared = not (req.parq_heart_condition or req.parq_joint_issues or req.parq_medications)

    # BREQ-2 motivation
    if req.motivation_external is not None:
        profile.motivation_external = Decimal(str(req.motivation_external))
    if req.motivation_introjected is not None:
        profile.motivation_introjected = Decimal(str(req.motivation_introjected))
    if req.motivation_identified is not None:
        profile.motivation_identified = Decimal(str(req.motivation_identified))
    if req.motivation_intrinsic is not None:
        profile.motivation_intrinsic = Decimal(str(req.motivation_intrinsic))
    if req.motivation_amotivation is not None:
        profile.motivation_amotivation = Decimal(str(req.motivation_amotivation))

    # Calculate RAI
    if all(v is not None for v in [
        req.motivation_amotivation, req.motivation_external,
        req.motivation_introjected, req.motivation_identified, req.motivation_intrinsic,
    ]):
        rai = (
            -3 * req.motivation_amotivation
            + -2 * req.motivation_external
            + -1 * req.motivation_introjected
            + 2 * req.motivation_identified
            + 3 * req.motivation_intrinsic
        )
        profile.motivation_rai = Decimal(str(round(rai, 1)))

    # Preferences
    profile.activity_preferences = req.activity_preferences
    profile.equipment_access = req.equipment_access
    profile.days_per_week = req.days_per_week
    profile.minutes_per_session = req.minutes_per_session
    profile.phase2_completed = True

    await db.flush()

    parq_warning = None
    if not profile.parq_cleared:
        parq_warning = "We recommend checking with your doctor before starting a new exercise program."

    return {"status": "ok", "phase2_completed": True, "parq_warning": parq_warning}


@router.get("/recommendations")
async def get_resource_recommendations(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    recs = await get_recommendations(db, user.id)
    return {"recommendations": recs}
