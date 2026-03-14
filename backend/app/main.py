from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.routers.auth import router as auth_router
from app.routers.onboarding import router as onboarding_router
from app.routers.activities import router as activities_router
from app.routers.food import router as food_router
from app.routers.points import router as points_router, rewards_router
from app.routers.integrations import router as integrations_router
from app.routers.programs import router as programs_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await seed_resources()
    yield


app = FastAPI(title="Fitness Rewards", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(onboarding_router)
app.include_router(activities_router)
app.include_router(food_router)
app.include_router(points_router)
app.include_router(rewards_router)
app.include_router(integrations_router)
app.include_router(programs_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "0.1.0"}


async def seed_resources():
    """Seed the resource library with curated fitness programs."""
    from app.database import async_session
    from app.models.resource import Resource
    from sqlalchemy import select

    async with async_session() as db:
        existing = await db.execute(select(Resource).limit(1))
        if existing.scalar_one_or_none():
            return  # Already seeded

        resources = [
            Resource(
                name="Darebee Foundation Program",
                source="darebee",
                url="https://darebee.com/programs/foundation-program.html",
                description="30-day beginner program. Bodyweight exercises, no equipment needed. Perfect starting point.",
                goal_tags=["get_active", "feel_better"],
                activity_tags=["bodyweight"],
                equipment_needed="none",
                ttm_stages=["precontemplation", "contemplation", "preparation"],
                difficulty="beginner",
                duration_days=30,
            ),
            Resource(
                name="Darebee 30 Days of Change",
                source="darebee",
                url="https://darebee.com/programs/30-days-of-change.html",
                description="30-day progressive program for building fitness habits. Bodyweight only.",
                goal_tags=["get_active", "lose_weight", "feel_better"],
                activity_tags=["bodyweight"],
                equipment_needed="none",
                ttm_stages=["contemplation", "preparation"],
                difficulty="beginner",
                duration_days=30,
            ),
            Resource(
                name="Darebee IRONHEART",
                source="darebee",
                url="https://darebee.com/programs/ironheart.html",
                description="Strength-focused bodyweight program. No equipment, all levels.",
                goal_tags=["build_strength"],
                activity_tags=["bodyweight"],
                equipment_needed="none",
                ttm_stages=["preparation", "action"],
                difficulty="intermediate",
                duration_days=30,
            ),
            Resource(
                name="Darebee Total Body Strength",
                source="darebee",
                url="https://darebee.com/programs/total-body-strength.html",
                description="Comprehensive strength building program using bodyweight.",
                goal_tags=["build_strength"],
                activity_tags=["bodyweight"],
                equipment_needed="none",
                ttm_stages=["action", "maintenance"],
                difficulty="intermediate",
                duration_days=30,
            ),
            Resource(
                name="Darebee 8 Weeks to 5K",
                source="darebee",
                url="https://darebee.com/programs/8-weeks-to-5k-program.html",
                description="Progressive running program from beginner to 5K in 8 weeks.",
                goal_tags=["get_active", "lose_weight"],
                activity_tags=["running"],
                equipment_needed="none",
                ttm_stages=["preparation", "action"],
                difficulty="beginner",
                duration_days=56,
            ),
            Resource(
                name="StrongLifts 5x5",
                source="stronglifts",
                url="https://stronglifts.com/5x5/",
                description="Simple barbell strength program. 3 days/week, 5 exercises, progressive overload.",
                goal_tags=["build_strength"],
                activity_tags=["weights"],
                equipment_needed="full_gym",
                ttm_stages=["preparation", "action", "maintenance"],
                difficulty="beginner",
                duration_days=90,
            ),
            Resource(
                name="Darebee 30 Days of Cardio",
                source="darebee",
                url="https://darebee.com/programs/30-days-of-cardio.html",
                description="30-day cardio program, no equipment. Great for weight loss.",
                goal_tags=["lose_weight", "get_active"],
                activity_tags=["bodyweight"],
                equipment_needed="none",
                ttm_stages=["preparation", "action"],
                difficulty="beginner",
                duration_days=30,
            ),
            Resource(
                name="Darebee POWERBUILDER",
                source="darebee",
                url="https://darebee.com/programs/powerbuilder-program.html",
                description="Advanced strength and power program using bodyweight.",
                goal_tags=["build_strength"],
                activity_tags=["bodyweight"],
                equipment_needed="none",
                ttm_stages=["action", "maintenance"],
                difficulty="advanced",
                duration_days=30,
            ),
            Resource(
                name="Fitness Blender (YouTube)",
                source="youtube",
                url="https://www.youtube.com/@fitnessblender",
                description="Free workout videos for all levels. Huge variety: HIIT, strength, yoga, pilates.",
                goal_tags=["lose_weight", "build_strength", "get_active", "feel_better"],
                activity_tags=["bodyweight", "yoga"],
                equipment_needed="none",
                ttm_stages=["contemplation", "preparation", "action", "maintenance"],
                difficulty="beginner",
                duration_days=None,
            ),
            Resource(
                name="Darebee Yoga Flexibility Program",
                source="darebee",
                url="https://darebee.com/programs/flexibility-program.html",
                description="30-day flexibility and yoga program for beginners.",
                goal_tags=["feel_better"],
                activity_tags=["yoga"],
                equipment_needed="none",
                ttm_stages=["precontemplation", "contemplation", "preparation"],
                difficulty="beginner",
                duration_days=30,
            ),
        ]

        for r in resources:
            db.add(r)
        await db.commit()
