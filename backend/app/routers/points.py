from typing import Annotated
from datetime import date
import uuid as uuid_mod
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.points import PointRule, DailyTarget
from app.models.reward import Reward
from app.schemas.points import PointRuleUpdate, DailyTargetUpdate
from app.schemas.reward import RewardCreate, RewardRedeemRequest
from app.utils.auth import get_current_user
from app.services.points_engine import get_today_status, get_weekly_summary, redeem_reward

router = APIRouter(prefix="/api/points", tags=["points"])


@router.get("/today")
async def today_status(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    return await get_today_status(db, user.id)


@router.get("/week")
async def week_summary(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    start: date | None = None,
):
    d = start or date.today()
    return await get_weekly_summary(db, user.id, d)


@router.get("/rules")
async def list_rules(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(PointRule).where(PointRule.user_id == user.id))
    rules = result.scalars().all()
    return [
        {"id": str(r.id), "category": r.category, "description": r.description,
         "points": r.points, "unit": r.unit, "is_active": r.is_active}
        for r in rules
    ]


@router.patch("/rules/{rule_id}")
async def update_rule(
    rule_id: str,
    req: PointRuleUpdate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(
        select(PointRule).where(PointRule.id == uuid_mod.UUID(rule_id), PointRule.user_id == user.id)
    )
    rule = result.scalar_one_or_none()
    if not rule:
        raise HTTPException(status_code=404)
    if req.points is not None:
        rule.points = req.points
    if req.description is not None:
        rule.description = req.description
    if req.is_active is not None:
        rule.is_active = req.is_active
    await db.flush()
    return {"status": "updated"}


@router.get("/targets")
async def get_targets(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(DailyTarget).where(DailyTarget.user_id == user.id))
    t = result.scalar_one_or_none()
    if not t:
        return {"daily_minimum_pts": 80, "weekly_target_pts": 500, "weekly_bonus_pts": 50}
    return {"daily_minimum_pts": t.daily_minimum_pts, "weekly_target_pts": t.weekly_target_pts, "weekly_bonus_pts": t.weekly_bonus_pts}


@router.patch("/targets")
async def update_targets(
    req: DailyTargetUpdate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(DailyTarget).where(DailyTarget.user_id == user.id))
    t = result.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404)
    if req.daily_minimum_pts is not None:
        t.daily_minimum_pts = req.daily_minimum_pts
    if req.weekly_target_pts is not None:
        t.weekly_target_pts = req.weekly_target_pts
    if req.weekly_bonus_pts is not None:
        t.weekly_bonus_pts = req.weekly_bonus_pts
    await db.flush()
    return {"status": "updated"}


# --- Rewards ---
rewards_router = APIRouter(prefix="/api/rewards", tags=["rewards"])


@rewards_router.get("")
async def list_rewards(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(Reward).where(Reward.user_id == user.id).order_by(Reward.created_at))
    rewards = result.scalars().all()
    return [
        {"id": str(r.id), "name": r.name, "description": r.description,
         "point_cost": r.point_cost, "is_active": r.is_active}
        for r in rewards
    ]


@rewards_router.post("")
async def create_reward(
    req: RewardCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    reward = Reward(user_id=user.id, name=req.name, description=req.description, point_cost=req.point_cost)
    db.add(reward)
    await db.flush()
    return {"id": str(reward.id), "name": reward.name, "point_cost": reward.point_cost}


@rewards_router.post("/{reward_id}/redeem")
async def redeem(
    reward_id: str,
    req: RewardRedeemRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await redeem_reward(db, user.id, uuid_mod.UUID(reward_id), req.date)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["reason"])
    return result
