from __future__ import annotations

"""Resource recommendation engine — matches external programs to user profiles."""
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.resource import Resource
from app.models.profile import UserProfile


# Equipment categories that satisfy each resource requirement
EQUIPMENT_SATISFIES = {
    "none": set(),  # bodyweight — always available
    "basic_home": {"dumbbells", "resistance_bands", "pull_up_bar", "kettlebell"},
    "full_gym": {"barbell", "squat_rack", "bench_press", "machines", "cable_machine", "dumbbells"},
}


async def get_recommendations(db: AsyncSession, user_id: uuid.UUID) -> list[dict]:
    profile_result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile:
        return []

    query = select(Resource).where(Resource.is_active == True)

    # Filter by equipment: if user has specific equipment, determine what resource levels they can do
    user_equipment = set(profile.equipment_list or [])
    if not user_equipment:
        # No equipment selected — only show bodyweight programs
        query = query.where(Resource.equipment_needed == "none")
    elif user_equipment & EQUIPMENT_SATISFIES["full_gym"]:
        # Has gym-level equipment — show everything
        pass
    elif user_equipment & EQUIPMENT_SATISFIES["basic_home"]:
        # Has some home equipment — show none + basic_home
        query = query.where(Resource.equipment_needed.in_(["none", "basic_home"]))
    else:
        # Only has non-gym items (bicycle, pool, etc.) — show bodyweight
        query = query.where(Resource.equipment_needed == "none")

    result = await db.execute(query)
    resources = result.scalars().all()

    user_prefs = set(profile.activity_preferences or [])
    user_goal = profile.primary_goal
    user_stage = profile.ttm_stage

    difficulty_map = {
        "precontemplation": "beginner",
        "contemplation": "beginner",
        "preparation": "beginner",
        "action": "intermediate",
        "maintenance": "advanced",
    }

    scored = []
    for r in resources:
        score = 0
        if user_goal and user_goal in (r.goal_tags or []):
            score += 30
        overlap = user_prefs & set(r.activity_tags or [])
        score += len(overlap) * 15
        if user_stage and user_stage in (r.ttm_stages or []):
            score += 20
        if r.difficulty == difficulty_map.get(user_stage):
            score += 10
        scored.append((r, score))

    scored.sort(key=lambda x: x[1], reverse=True)

    return [
        {
            "id": str(r.id),
            "name": r.name,
            "source": r.source,
            "url": r.url,
            "description": r.description,
            "difficulty": r.difficulty,
            "duration_days": r.duration_days,
            "goal_tags": r.goal_tags,
            "activity_tags": r.activity_tags,
            "score": s,
        }
        for r, s in scored[:8]
    ]
