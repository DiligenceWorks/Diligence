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


# ── Program Tracking Endpoints ─────────────────────────────────────────────

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

    # Get all catalog workouts
    result = await db.execute(
        select(CatalogWorkout)
        .where(CatalogWorkout.catalog_id == program.catalog_id)
        .order_by(CatalogWorkout.week_number, CatalogWorkout.day_number)
    )
    workouts = result.scalars().all()

    # Get completed workout IDs
    result = await db.execute(
        select(WorkoutLog.catalog_workout_id).where(
            WorkoutLog.program_id == program.id,
            WorkoutLog.user_id == user.id,
        )
    )
    completed_ids = {row[0] for row in result.all()}

    # Calculate current position based on start date
    today = date.today()
    days_elapsed = (today - program.start_date).days
    current_week = (days_elapsed // 7) + 1
    current_day_of_week = (days_elapsed % 7) + 1  # 1=Mon, 7=Sun

    schedule = []
    today_workout = None

    for w in workouts:
        entry = {
            "id": str(w.id),
            "week_number": w.week_number,
            "day_number": w.day_number,
            "workout_name": w.workout_name,
            "exercises": w.exercises,
            "rest_day": w.rest_day,
            "notes": w.notes,
            "completed": w.id in completed_ids,
        }
        schedule.append(entry)

        if w.week_number == current_week and w.day_number == current_day_of_week:
            today_workout = entry

    # Get catalog details for progression rules
    result = await db.execute(
        select(ProgramCatalog).where(ProgramCatalog.id == program.catalog_id)
    )
    catalog = result.scalar_one_or_none()

    return {
        "program_id": str(program.id),
        "program_name": program.name,
        "start_date": program.start_date.isoformat(),
        "end_date": program.end_date.isoformat(),
        "current_week": current_week,
        "current_day_of_week": current_day_of_week,
        "today_workout": today_workout,
        "schedule": schedule,
        "total_workouts": len([w for w in workouts if not w.rest_day]),
        "completed_workouts": len(completed_ids),
        "progression_rules": catalog.progression_rules if catalog else None,
    }


@router.get("/{program_id}/workout/{workout_id}")
async def get_workout_detail(
    program_id: str,
    workout_id: str,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """Get a specific workout's full exercise details."""
    # Verify program belongs to user
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
            CatalogWorkout.id == uuid_mod.UUID(workout_id),
            CatalogWorkout.catalog_id == program.catalog_id,
        )
    )
    workout = result.scalar_one_or_none()
    if not workout:
        raise HTTPException(status_code=404)

    # Check if already completed
    result = await db.execute(
        select(WorkoutLog).where(
            WorkoutLog.program_id == program.id,
            WorkoutLog.catalog_workout_id == workout.id,
            WorkoutLog.user_id == user.id,
        )
    )
    log = result.scalar_one_or_none()

    return {
        "id": str(workout.id),
        "week_number": workout.week_number,
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
    """Mark a program workout as complete. Awards bonus points."""
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
            CatalogWorkout.id == uuid_mod.UUID(workout_id),
            CatalogWorkout.catalog_id == program.catalog_id,
        )
    )
    workout = result.scalar_one_or_none()
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")

    # Check not already completed
    result = await db.execute(
        select(WorkoutLog).where(
            WorkoutLog.program_id == program.id,
            WorkoutLog.catalog_workout_id == workout.id,
            WorkoutLog.user_id == user.id,
        )
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Workout already completed")

    # Award points — program workouts get 75 pts (vs 50 for generic)
    PROGRAM_WORKOUT_POINTS = 75

    # Log the workout completion
    log = WorkoutLog(
        user_id=user.id,
        program_id=program.id,
        catalog_workout_id=workout.id,
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
        title=f"{program.name}: {workout.workout_name or f'Week {workout.week_number} Day {workout.day_number}'}",
        description=f"Completed program workout ({len(workout.exercises)} exercises)",
        source="program",
        program_id=program.id,
        program_day=workout.day_number,
        metadata={"catalog_workout_id": str(workout.id), "program_points": True},
    )

    # Override points with program bonus if higher
    if activity.points_earned < PROGRAM_WORKOUT_POINTS:
        activity.points_earned = PROGRAM_WORKOUT_POINTS

    await db.flush()

    # Check for weekly bonus (all workouts in current week completed)
    weekly_bonus = await check_weekly_bonus(db, user, program, workout.week_number)

    # Check for program completion bonus
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
    db: AsyncSession, user: User, program: Program, week_number: int
) -> int:
    """Check if all workouts for a week are completed. Returns bonus points."""
    WEEKLY_BONUS = 50

    # Count total non-rest workouts in this week
    result = await db.execute(
        select(func.count(CatalogWorkout.id)).where(
            CatalogWorkout.catalog_id == program.catalog_id,
            CatalogWorkout.week_number == week_number,
            CatalogWorkout.rest_day == False,
        )
    )
    total_in_week = result.scalar() or 0
    if total_in_week == 0:
        return 0

    # Count completed in this week
    result = await db.execute(
        select(func.count(WorkoutLog.id))
        .join(CatalogWorkout, WorkoutLog.catalog_workout_id == CatalogWorkout.id)
        .where(
            WorkoutLog.program_id == program.id,
            WorkoutLog.user_id == user.id,
            CatalogWorkout.week_number == week_number,
        )
    )
    completed_in_week = result.scalar() or 0

    if completed_in_week >= total_in_week:
        # Award weekly bonus as an activity
        await log_activity_with_points(
            db=db,
            user_id=user.id,
            category="bonus",
            activity_date=date.today(),
            title=f"{program.name}: Week {week_number} Complete!",
            source="program",
            program_id=program.id,
            metadata={"weekly_bonus": True, "week": week_number},
        )
        return WEEKLY_BONUS

    return 0


async def check_completion_bonus(
    db: AsyncSession, user: User, program: Program
) -> int:
    """Check if all program workouts are completed. Returns bonus points."""
    COMPLETION_BONUS = 200

    # Count total non-rest workouts in program
    result = await db.execute(
        select(func.count(CatalogWorkout.id)).where(
            CatalogWorkout.catalog_id == program.catalog_id,
            CatalogWorkout.rest_day == False,
        )
    )
    total = result.scalar() or 0

    # Count completed
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
    """Program progress overview."""
    result = await db.execute(
        select(Program).where(
            Program.id == uuid_mod.UUID(program_id),
            Program.user_id == user.id,
        )
    )
    program = result.scalar_one_or_none()
    if not program or not program.catalog_id:
        raise HTTPException(status_code=404)

    # Total workouts
    result = await db.execute(
        select(func.count(CatalogWorkout.id)).where(
            CatalogWorkout.catalog_id == program.catalog_id,
            CatalogWorkout.rest_day == False,
        )
    )
    total = result.scalar() or 0

    # Completed
    result = await db.execute(
        select(func.count(WorkoutLog.id)).where(
            WorkoutLog.program_id == program.id,
            WorkoutLog.user_id == user.id,
        )
    )
    completed = result.scalar() or 0

    # Total points from this program
    result = await db.execute(
        select(func.coalesce(func.sum(WorkoutLog.points_earned), 0)).where(
            WorkoutLog.program_id == program.id,
            WorkoutLog.user_id == user.id,
        )
    )
    total_points = result.scalar() or 0

    today = date.today()
    days_elapsed = (today - program.start_date).days
    current_week = (days_elapsed // 7) + 1

    return {
        "program_id": str(program.id),
        "name": program.name,
        "status": program.status,
        "start_date": program.start_date.isoformat(),
        "end_date": program.end_date.isoformat(),
        "current_week": current_week,
        "total_workouts": total,
        "completed_workouts": completed,
        "completion_pct": round((completed / total * 100) if total > 0 else 0, 1),
        "total_points_earned": total_points,
    }
