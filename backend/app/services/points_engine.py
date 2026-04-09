from __future__ import annotations

"""Points calculation engine — the heart of the reward system."""
import uuid
from datetime import date, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import ActivityLog
from app.models.points import PointRule, DailyTarget
from app.models.reward import Reward, RewardRedemption
from app.models.program import Program
from app.utils.dates import get_week_boundaries


async def get_daily_points_earned(db: AsyncSession, user_id: uuid.UUID, d: date) -> int:
    result = await db.execute(
        select(func.coalesce(func.sum(ActivityLog.points_earned), 0))
        .where(ActivityLog.user_id == user_id, ActivityLog.activity_date == d)
    )
    return result.scalar()


async def get_daily_points_spent(db: AsyncSession, user_id: uuid.UUID, d: date) -> int:
    result = await db.execute(
        select(func.coalesce(func.sum(RewardRedemption.points_spent), 0))
        .where(RewardRedemption.user_id == user_id, RewardRedemption.redemption_date == d)
    )
    return result.scalar()


async def get_daily_target(db: AsyncSession, user_id: uuid.UUID) -> DailyTarget | None:
    result = await db.execute(
        select(DailyTarget).where(DailyTarget.user_id == user_id, DailyTarget.is_active == True)
    )
    return result.scalar_one_or_none()


async def get_week_points(db: AsyncSession, user_id: uuid.UUID, d: date) -> int:
    mon, sun = get_week_boundaries(d)
    result = await db.execute(
        select(func.coalesce(func.sum(ActivityLog.points_earned), 0))
        .where(
            ActivityLog.user_id == user_id,
            ActivityLog.activity_date >= mon,
            ActivityLog.activity_date <= sun,
        )
    )
    return result.scalar()


async def get_activities_for_date(db: AsyncSession, user_id: uuid.UUID, d: date) -> list[dict]:
    result = await db.execute(
        select(ActivityLog)
        .where(ActivityLog.user_id == user_id, ActivityLog.activity_date == d)
        .order_by(ActivityLog.logged_at.desc())
    )
    activities = result.scalars().all()
    return [
        {
            "id": str(a.id),
            "category": a.category,
            "title": a.title,
            "points_earned": a.points_earned,
            "duration_minutes": a.duration_minutes,
            "source": a.source,
            "logged_at": a.logged_at.isoformat() if a.logged_at else None,
        }
        for a in activities
    ]


async def get_available_rewards(db: AsyncSession, user_id: uuid.UUID) -> list[dict]:
    result = await db.execute(
        select(Reward).where(Reward.user_id == user_id, Reward.is_active == True)
    )
    rewards = result.scalars().all()
    return [
        {"id": str(r.id), "name": r.name, "point_cost": r.point_cost, "description": r.description}
        for r in rewards
    ]


async def get_active_program(db: AsyncSession, user_id: uuid.UUID) -> dict | None:
    result = await db.execute(
        select(Program)
        .where(Program.user_id == user_id, Program.status == "active")
        .order_by(Program.created_at.desc())
    )
    program = result.scalar_one_or_none()
    if not program:
        return None
    today = date.today()
    day_num = (today - program.start_date).days + 1
    total = (program.end_date - program.start_date).days + 1
    return {
        "id": str(program.id),
        "name": program.name,
        "day": min(day_num, total),
        "total_days": total,
        "start_date": program.start_date.isoformat(),
        "end_date": program.end_date.isoformat(),
        "status": program.status,
    }


async def get_today_status(db: AsyncSession, user_id: uuid.UUID) -> dict:
    today = date.today()
    earned = await get_daily_points_earned(db, user_id, today)
    target = await get_daily_target(db, user_id)
    daily_min = target.daily_minimum_pts if target else 80
    weekly_tgt = target.weekly_target_pts if target else 500
    gate_passed = earned >= daily_min
    activities = await get_activities_for_date(db, user_id, today)
    rewards = await get_available_rewards(db, user_id) if gate_passed else []
    week_pts = await get_week_points(db, user_id, today)
    program = await get_active_program(db, user_id)

    return {
        "date": today.isoformat(),
        "points_earned": earned,
        "daily_minimum": daily_min,
        "gate_passed": gate_passed,
        "points_remaining": max(0, daily_min - earned),
        "activities_today": activities,
        "rewards_available": rewards,
        "week_points": week_pts,
        "weekly_target": weekly_tgt,
        "program_id": program["id"] if program else None,
        "program_day": program["day"] if program else None,
        "program_total_days": program["total_days"] if program else None,
        "program_name": program["name"] if program else None,
    }


async def log_activity_with_points(
    db: AsyncSession,
    user_id: uuid.UUID,
    category: str,
    activity_date: date,
    title: str | None = None,
    description: str | None = None,
    duration_minutes: int | None = None,
    source: str = "manual",
    external_id: str | None = None,
    program_id: uuid.UUID | None = None,
    program_day: int | None = None,
    metadata: dict | None = None,
) -> ActivityLog:
    """Log an activity and auto-calculate points from active rules."""
    # Find matching point rule
    result = await db.execute(
        select(PointRule).where(
            PointRule.user_id == user_id,
            PointRule.category == category,
            PointRule.is_active == True,
        )
    )
    rule = result.scalar_one_or_none()

    points = 0
    rule_id = None
    if rule:
        rule_id = rule.id
        if rule.unit == "per_hour" and duration_minutes:
            points = rule.points * (duration_minutes / 60)
        else:
            points = rule.points

    activity = ActivityLog(
        user_id=user_id,
        category=category,
        title=title,
        description=description,
        duration_minutes=duration_minutes,
        source=source,
        external_id=external_id,
        points_earned=int(points),
        rule_id=rule_id,
        activity_date=activity_date,
        program_id=program_id,
        program_day=program_day,
        metadata_json=metadata or {},
    )
    db.add(activity)
    await db.flush()
    return activity


async def redeem_reward(
    db: AsyncSession, user_id: uuid.UUID, reward_id: uuid.UUID, redemption_date: date | None = None
) -> dict:
    """Attempt to redeem a reward. Returns success/failure with details."""
    d = redemption_date or date.today()
    earned = await get_daily_points_earned(db, user_id, d)
    target = await get_daily_target(db, user_id)
    daily_min = target.daily_minimum_pts if target else 80

    if earned < daily_min:
        return {"success": False, "reason": f"Need {daily_min} points today, have {earned}"}

    result = await db.execute(select(Reward).where(Reward.id == reward_id, Reward.user_id == user_id))
    reward = result.scalar_one_or_none()
    if not reward:
        return {"success": False, "reason": "Reward not found"}

    redemption = RewardRedemption(
        user_id=user_id,
        reward_id=reward_id,
        points_spent=reward.point_cost,
        redemption_date=d,
    )
    db.add(redemption)
    await db.flush()

    return {
        "success": True,
        "id": str(redemption.id),
        "reward_name": reward.name,
        "points_spent": reward.point_cost,
        "redemption_date": d.isoformat(),
    }


async def get_weekly_summary(db: AsyncSession, user_id: uuid.UUID, d: date) -> dict:
    """Generate weekly summary for the week containing date d."""
    mon, sun = get_week_boundaries(d)
    target = await get_daily_target(db, user_id)
    daily_min = target.daily_minimum_pts if target else 80
    weekly_tgt = target.weekly_target_pts if target else 500
    bonus = target.weekly_bonus_pts if target else 50

    daily_breakdown = []
    total_earned = 0
    total_spent = 0
    active_days = 0
    gate_days = 0

    for i in range(7):
        day = mon + timedelta(days=i)
        earned = await get_daily_points_earned(db, user_id, day)
        spent = await get_daily_points_spent(db, user_id, day)
        gate = earned >= daily_min
        total_earned += earned
        total_spent += spent
        if earned > 0:
            active_days += 1
        if gate:
            gate_days += 1
        daily_breakdown.append({
            "date": day.isoformat(),
            "points_earned": earned,
            "points_spent": spent,
            "gate_passed": gate,
            "daily_minimum": daily_min,
        })

    hit_target = total_earned >= weekly_tgt

    return {
        "week_start": mon.isoformat(),
        "week_end": sun.isoformat(),
        "total_points_earned": total_earned,
        "total_points_spent": total_spent,
        "active_days": active_days,
        "gate_passed_days": gate_days,
        "hit_weekly_target": hit_target,
        "weekly_target": weekly_tgt,
        "weekly_bonus_earned": bonus if hit_target else 0,
        "daily_breakdown": daily_breakdown,
    }
