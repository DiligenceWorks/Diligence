"""Catalog router — program research, browsing, adoption, and workout tracking."""
from __future__ import annotations

import uuid as uuid_mod
from datetime import date, timedelta, datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models.user import User
from app.models.program import Program
from app.models.catalog import ProgramCatalog, CatalogWorkout, CrawlQueue, WorkoutLog
from app.services.program_research import slugify, find_urls_for_program
from app.services.points_engine import log_activity_with_points
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/programs", tags=["programs-v2"])


# ── Schemas ─────────────────────────────────────────────────────────────────

class ResearchRequest(BaseModel):
    name: str

class AdoptRequest(BaseModel):
    start_date: date

class CompleteWorkoutRequest(BaseModel):
    exercises_completed: list[dict] | None = None
    notes: str | None = None


# ── Catalog Endpoints ───────────────────────────────────────────────────────

@router.get("/catalog")
async def list_catalog(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    q: str | None = None,
):
    """List all programs in catalog, optionally filtered by search query."""
    query = select(ProgramCatalog).order_by(ProgramCatalog.created_at.desc())
    if q:
        query = query.where(ProgramCatalog.name.ilike(f"%{q}%"))

    result = await db.execute(query)
    programs = result.scalars().all()

    return [
        {
            "id": str(p.id),
            "name": p.name,
            "slug": p.slug,
            "description": p.description,
            "duration_weeks": p.duration_weeks,
            "frequency_per_week": p.frequency_per_week,
            "equipment": p.equipment or [],
            "difficulty": p.difficulty,
            "category": p.category,
            "crawl_status": p.crawl_status,
            "source_url": p.source_url,
        }
        for p in programs
    ]


@router.get("/catalog/{catalog_id}")
async def get_catalog_program(
    catalog_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get full catalog program detail including workouts."""
    result = await db.execute(
        select(ProgramCatalog)
        .options(selectinload(ProgramCatalog.workouts))
        .where(ProgramCatalog.id == uuid_mod.UUID(catalog_id))
    )
    p = result.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Program not found in catalog")

    workouts = []
    for w in p.workouts:
        workouts.append({
            "id": str(w.id),
            "week_number": w.week_number,
            "day_number": w.day_number,
            "workout_name": w.workout_name,
            "exercises": w.exercises,
            "notes": w.notes,
            "rest_day": w.rest_day,
        })

    return {
        "id": str(p.id),
        "name": p.name,
        "description": p.description,
        "duration_weeks": p.duration_weeks,
        "frequency_per_week": p.frequency_per_week,
        "equipment": p.equipment or [],
        "difficulty": p.difficulty,
        "category": p.category,
        "progression_rules": p.progression_rules,
        "source_url": p.source_url,
        "crawl_status": p.crawl_status,
        "crawl_error": p.crawl_error,
        "workouts": workouts,
    }


@router.post("/research")
async def research_program(
    req: ResearchRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Submit a program name for research. Creates catalog entry + crawl job."""
    slug = slugify(req.name)

    # Check if already in catalog
    result = await db.execute(
        select(ProgramCatalog).where(ProgramCatalog.slug == slug)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return {
            "id": str(existing.id),
            "name": existing.name,
            "crawl_status": existing.crawl_status,
            "already_exists": True,
        }

    # Find URLs
    urls = find_urls_for_program(req.name)

    # Create catalog entry
    catalog = ProgramCatalog(
        name=req.name.strip(),
        slug=slug,
        crawl_status="pending",
        source_url=urls[0] if urls else None,
    )
    db.add(catalog)
    await db.flush()

    # Create crawl job
    job = CrawlQueue(
        catalog_id=catalog.id,
        search_query=req.name.strip(),
        priority="low",
        urls_to_crawl=urls,
    )
    db.add(job)
    await db.flush()

    return {
        "id": str(catalog.id),
        "name": catalog.name,
        "crawl_status": catalog.crawl_status,
        "already_exists": False,
        "urls_found": len(urls),
        "message": "Program queued for research. It will be processed during off-peak hours."
        if not urls
        else f"Program queued for research with {len(urls)} known source(s).",
    }


@router.post("/catalog/{catalog_id}/adopt")
async def adopt_program(
    catalog_id: str,
    req: AdoptRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """User adopts a catalog program — creates their personal program enrollment."""
    result = await db.execute(
        select(ProgramCatalog).where(
            ProgramCatalog.id == uuid_mod.UUID(catalog_id),
            ProgramCatalog.crawl_status == "ready",
        )
    )
    catalog = result.scalar_one_or_none()
    if not catalog:
        raise HTTPException(
            status_code=404,
            detail="Program not found or not ready yet"
        )

    # Check if user already has this program active
    result = await db.execute(
        select(Program).where(
            Program.user_id == user.id,
            Program.catalog_id == uuid_mod.UUID(catalog_id),
            Program.status == "active",
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="You already have this program active")

    # Calculate end date
    duration_weeks = catalog.duration_weeks or 12
    end_date = req.start_date + timedelta(weeks=duration_weeks)

    program = Program(
        user_id=user.id,
        name=catalog.name,
        source="catalog",
        source_url=catalog.source_url,
        start_date=req.start_date,
        end_date=end_date,
        status="active",
        catalog_id=catalog.id,
        current_week=1,
        current_day=1,
    )
    db.add(program)
    await db.flush()

    return {
        "id": str(program.id),
        "name": program.name,
        "start_date": program.start_date.isoformat(),
        "end_date": program.end_date.isoformat(),
        "catalog_id": str(catalog.id),
    }


# ── Program Tracking Endpoints ────────────────────────────────────────────────
#
# Workout ID encoding:
#   The catalog stores a TEMPLATE (typically week 1 only), and the program
#   rotates that template across `duration_weeks` real weeks. To allow the same
#   template workout to be completed once per real week, schedule entries use
#   a synthetic ID format: "{template_uuid}::{real_week}".
#
#   Frontend treats the ID as opaque. Backend parses it on every workout
#   endpoint to recover (template_workout_id, real_week_number).

def _make_workout_id(template_id: uuid_mod.UUID, real_week: int) -> str:
    return f"{template_id}::{real_week}"

def _parse_workout_id(workout_id: str) -> tuple[uuid_mod.UUID, int]:
    """Parse a synthetic workout ID. Falls back to (uuid, 1) for legacy IDs."""
    if "::" in workout_id:
        uuid_part, week_part = workout_id.split("::", 1)
        return uuid_mod.UUID(uuid_part), int(week_part)
    return uuid_mod.UUID(workout_id), 1


async def _load_template_workouts(db: AsyncSession, catalog_id: uuid_mod.UUID):
    """Returns (template_workouts_list, template_weeks_count)."""
    result = await db.execute(
        select(CatalogWorkout)
        .where(CatalogWorkout.catalog_id == catalog_id)
        .order_by(CatalogWorkout.week_number, CatalogWorkout.day_number)
    )
    workouts = result.scalars().all()
    template_weeks = max((w.week_number for w in workouts), default=1)
    return workouts, template_weeks


def _build_rotated_schedule(template_workouts, template_weeks, total_weeks, completed_keys):
    """
    Generate the full rotated schedule across `total_weeks` real program weeks.
    `completed_keys` is a set of (catalog_workout_id, week_number) tuples.
    Returns list of schedule entry dicts.
    """
    schedule = []
    for real_week in range(1, total_weeks + 1):
        template_week = ((real_week - 1) % template_weeks) + 1
        for w in template_workouts:
            if w.week_number != template_week:
                continue
            schedule.append({
                "id": _make_workout_id(w.id, real_week),
                "template_id": str(w.id),
                "week_number": real_week,
                "day_number": w.day_number,
                "workout_name": w.workout_name,
                "exercises": w.exercises,
                "rest_day": w.rest_day,
                "notes": w.notes,
                "completed": (w.id, real_week) in completed_keys,
            })
    return schedule


@router.get("/{program_id}/schedule")
async def get_program_schedule(
    program_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get the user's program schedule — today's workout, upcoming, and completed."""
    result = await db.execute(
        select(Program).where(
            Program.id == uuid_mod.UUID(program_id),
            Program.user_id == user.id,
        )
    )
    program = result.scalar_one_or_none()
    if not program or not program.catalog_id:
        raise HTTPException(status_code=404)

    # Load catalog + template workouts
    result = await db.execute(
        select(ProgramCatalog).where(ProgramCatalog.id == program.catalog_id)
    )
    catalog = result.scalar_one_or_none()
    if not catalog:
        raise HTTPException(status_code=404, detail="Catalog program missing")

    template_workouts, template_weeks = await _load_template_workouts(db, program.catalog_id)
    if not template_workouts:
        raise HTTPException(status_code=404, detail="No workouts in catalog yet")

    total_weeks = catalog.duration_weeks or template_weeks

    # Completed (catalog_workout_id, week_number) pairs
    result = await db.execute(
        select(WorkoutLog.catalog_workout_id, WorkoutLog.week_number).where(
            WorkoutLog.program_id == program.id,
            WorkoutLog.user_id == user.id,
        )
    )
    completed_keys = {(row[0], row[1]) for row in result.all()}

    # Build full rotated schedule
    schedule = _build_rotated_schedule(
        template_workouts, template_weeks, total_weeks, completed_keys
    )

    # Calculate current real week from start date
    today = date.today()
    days_elapsed = max(0, (today - program.start_date).days)
    current_week = min(total_weeks, (days_elapsed // 7) + 1)

    # Today's workout: the first uncompleted, non-rest entry in the current real week.
    # This is more flexible than literal day-of-week matching — the user can do
    # any of the week's workouts on any calendar day.
    today_workout = None
    for entry in schedule:
        if entry["week_number"] == current_week and not entry["rest_day"] and not entry["completed"]:
            today_workout = entry
            break

    total_workouts = sum(1 for e in schedule if not e["rest_day"])
    completed_workouts = sum(1 for e in schedule if e["completed"] and not e["rest_day"])

    return {
        "program_id": str(program.id),
        "program_name": program.name,
        "start_date": program.start_date.isoformat(),
        "end_date": program.end_date.isoformat(),
        "current_week": current_week,
        "total_weeks": total_weeks,
        "today_workout": today_workout,
        "schedule": schedule,
        "total_workouts": total_workouts,
        "completed_workouts": completed_workouts,
        "progression_rules": catalog.progression_rules,
    }


@router.get("/{program_id}/workout/{workout_id}")
async def get_workout_detail(
    program_id: str,
    workout_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a specific workout's full exercise details (parses synthetic ID)."""
    template_id, real_week = _parse_workout_id(workout_id)

    result = await db.execute(
        select(Program).where(
            Program.id == uuid_mod.UUID(program_id),
            Program.user_id == user.id,
        )
    )
    program = result.scalar_one_or_none()
    if not program:
        raise HTTPException(status_code=404)

    result = await db.execute(
        select(CatalogWorkout).where(
            CatalogWorkout.id == template_id,
            CatalogWorkout.catalog_id == program.catalog_id,
        )
    )
    workout = result.scalar_one_or_none()
    if not workout:
        raise HTTPException(status_code=404)

    # Check completed for this specific real week
    result = await db.execute(
        select(WorkoutLog).where(
            WorkoutLog.program_id == program.id,
            WorkoutLog.catalog_workout_id == workout.id,
            WorkoutLog.week_number == real_week,
            WorkoutLog.user_id == user.id,
        )
    )
    log = result.scalar_one_or_none()

    return {
        "id": _make_workout_id(workout.id, real_week),
        "template_id": str(workout.id),
        "week_number": real_week,
        "day_number": workout.day_number,
        "workout_name": workout.workout_name,
        "exercises": workout.exercises,
        "rest_day": workout.rest_day,
        "notes": workout.notes,
        "completed": log is not None,
        "completed_at": log.completed_at.isoformat() if log else None,
        "exercises_completed": log.exercises_completed if log else None,
    }


@router.post("/{program_id}/workout/{workout_id}/complete")
async def complete_workout(
    program_id: str,
    workout_id: str,
    req: CompleteWorkoutRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Mark a program workout as complete (parses synthetic ID). Awards bonus points."""
    template_id, real_week = _parse_workout_id(workout_id)

    # Verify program
    result = await db.execute(
        select(Program).where(
            Program.id == uuid_mod.UUID(program_id),
            Program.user_id == user.id,
            Program.status == "active",
        )
    )
    program = result.scalar_one_or_none()
    if not program:
        raise HTTPException(status_code=404, detail="Active program not found")

    # Verify workout belongs to program's catalog
    result = await db.execute(
        select(CatalogWorkout).where(
            CatalogWorkout.id == template_id,
            CatalogWorkout.catalog_id == program.catalog_id,
        )
    )
    workout = result.scalar_one_or_none()
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")

    if workout.rest_day:
        raise HTTPException(status_code=400, detail="Cannot complete a rest day")

    # Check not already completed for THIS real week
    result = await db.execute(
        select(WorkoutLog).where(
            WorkoutLog.program_id == program.id,
            WorkoutLog.catalog_workout_id == workout.id,
            WorkoutLog.week_number == real_week,
            WorkoutLog.user_id == user.id,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Workout already completed for this week")

    PROGRAM_WORKOUT_POINTS = 75

    log = WorkoutLog(
        user_id=user.id,
        program_id=program.id,
        catalog_workout_id=workout.id,
        week_number=real_week,
        exercises_completed=req.exercises_completed,
        points_earned=PROGRAM_WORKOUT_POINTS,
        notes=req.notes,
    )
    db.add(log)

    # Also log as activity for the points engine
    activity = await log_activity_with_points(
        db=db,
        user_id=user.id,
        category="workout",
        activity_date=date.today(),
        title=f"{program.name}: Wk{real_week} {workout.workout_name or f'Day {workout.day_number}'}",
        description=f"Completed program workout ({len(workout.exercises)} exercises)",
        source="program",
        program_id=program.id,
        program_day=workout.day_number,
        metadata={
            "catalog_workout_id": str(workout.id),
            "real_week": real_week,
            "program_points": True,
        },
    )

    if activity.points_earned < PROGRAM_WORKOUT_POINTS:
        activity.points_earned = PROGRAM_WORKOUT_POINTS

    await db.flush()

    # Bonuses
    weekly_bonus = await check_weekly_bonus(db, user, program, real_week)
    completion_bonus = await check_completion_bonus(db, user, program)

    total_points = PROGRAM_WORKOUT_POINTS + weekly_bonus + completion_bonus

    return {
        "workout_log_id": str(log.id),
        "points_earned": PROGRAM_WORKOUT_POINTS,
        "weekly_bonus": weekly_bonus,
        "completion_bonus": completion_bonus,
        "total_points": total_points,
        "workout_name": workout.workout_name,
    }


async def check_weekly_bonus(
    db: AsyncSession, user: User, program: Program, real_week: int
) -> int:
    """Award bonus when all template workouts for the current real week are done."""
    WEEKLY_BONUS = 50

    # Get template metadata
    template_workouts, template_weeks = await _load_template_workouts(db, program.catalog_id)
    template_week = ((real_week - 1) % template_weeks) + 1
    week_template_workouts = [w for w in template_workouts if w.week_number == template_week and not w.rest_day]
    total_in_week = len(week_template_workouts)
    if total_in_week == 0:
        return 0

    # Count completed workout_logs for this real week
    template_ids = [w.id for w in week_template_workouts]
    result = await db.execute(
        select(func.count(WorkoutLog.id)).where(
            WorkoutLog.program_id == program.id,
            WorkoutLog.user_id == user.id,
            WorkoutLog.week_number == real_week,
            WorkoutLog.catalog_workout_id.in_(template_ids),
        )
    )
    completed_in_week = result.scalar() or 0

    if completed_in_week >= total_in_week:
        await log_activity_with_points(
            db=db,
            user_id=user.id,
            category="bonus",
            activity_date=date.today(),
            title=f"{program.name}: Week {real_week} Complete!",
            source="program",
            program_id=program.id,
            metadata={"weekly_bonus": True, "week": real_week},
        )
        return WEEKLY_BONUS

    return 0


async def check_completion_bonus(
    db: AsyncSession, user: User, program: Program
) -> int:
    """Award completion bonus when all (template × weeks) workouts done."""
    COMPLETION_BONUS = 200

    result = await db.execute(
        select(ProgramCatalog).where(ProgramCatalog.id == program.catalog_id)
    )
    catalog = result.scalar_one_or_none()
    if not catalog:
        return 0

    template_workouts, template_weeks = await _load_template_workouts(db, program.catalog_id)
    total_weeks = catalog.duration_weeks or template_weeks
    template_per_week = sum(1 for w in template_workouts if not w.rest_day) // max(1, template_weeks)
    total = template_per_week * total_weeks

    result = await db.execute(
        select(func.count(WorkoutLog.id)).where(
            WorkoutLog.program_id == program.id,
            WorkoutLog.user_id == user.id,
        )
    )
    completed = result.scalar() or 0

    if completed >= total and total > 0:
        program.status = "completed"
        await log_activity_with_points(
            db=db,
            user_id=user.id,
            category="bonus",
            activity_date=date.today(),
            title=f"{program.name}: Program Complete!",
            source="program",
            program_id=program.id,
            metadata={"completion_bonus": True},
        )
        return COMPLETION_BONUS

    return 0


@router.get("/{program_id}/progress")
async def get_program_progress(
    program_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Program progress overview — accounts for full template×weeks total."""
    result = await db.execute(
        select(Program).where(
            Program.id == uuid_mod.UUID(program_id),
            Program.user_id == user.id,
        )
    )
    program = result.scalar_one_or_none()
    if not program or not program.catalog_id:
        raise HTTPException(status_code=404)

    result = await db.execute(
        select(ProgramCatalog).where(ProgramCatalog.id == program.catalog_id)
    )
    catalog = result.scalar_one_or_none()

    template_workouts, template_weeks = await _load_template_workouts(db, program.catalog_id)
    total_weeks = (catalog.duration_weeks if catalog else None) or template_weeks
    template_non_rest = sum(1 for w in template_workouts if not w.rest_day)
    template_per_week = template_non_rest // max(1, template_weeks)
    total = template_per_week * total_weeks

    result = await db.execute(
        select(func.count(WorkoutLog.id)).where(
            WorkoutLog.program_id == program.id,
            WorkoutLog.user_id == user.id,
        )
    )
    completed = result.scalar() or 0

    result = await db.execute(
        select(func.coalesce(func.sum(WorkoutLog.points_earned), 0)).where(
            WorkoutLog.program_id == program.id,
            WorkoutLog.user_id == user.id,
        )
    )
    total_points = result.scalar() or 0

    today = date.today()
    days_elapsed = max(0, (today - program.start_date).days)
    current_week = min(total_weeks, (days_elapsed // 7) + 1)

    return {
        "program_id": str(program.id),
        "name": program.name,
        "status": program.status,
        "start_date": program.start_date.isoformat(),
        "end_date": program.end_date.isoformat(),
        "current_week": current_week,
        "total_weeks": total_weeks,
        "total_workouts": total,
        "completed_workouts": completed,
        "completion_pct": round((completed / total * 100) if total > 0 else 0, 1),
        "total_points_earned": total_points,
    }
