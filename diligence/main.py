from __future__ import annotations

import asyncio
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("diligence")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Retry DB init — container may start before postgres is ready
    for attempt in range(10):
        try:
            from diligence.database import init_db
            await init_db()
            logger.info("Database tables created successfully")
            break
        except Exception as e:
            logger.warning(f"DB init attempt {attempt + 1}/10 failed: {e}")
            if attempt < 9:
                await asyncio.sleep(3)
            else:
                logger.error("Could not initialize database after 10 attempts")

    # Fail fast if SECRET_KEY not configured
    from diligence.config import get_settings
    _s = get_settings()
    if _s.secret_key == "change-me-in-production":
        logger.error("CRITICAL: SECRET_KEY not set. Run ./setup.sh or set SECRET_KEY in .env")
        sys.exit(1)

    # Run lightweight migrations for schema changes
    try:
        await run_migrations()
        logger.info("Migrations completed")
    except Exception as e:
        logger.warning(f"Migration failed (non-fatal): {e}")

    # Seed resources
    try:
        await seed_resources()
        logger.info("Resource library seeded")
    except Exception as e:
        logger.warning(f"Resource seeding failed (non-fatal): {e}")

    # Start background crawl queue scheduler
    crawl_task = None
    if _s.crawl_enabled:
        try:
            from diligence.services.crawl_scheduler import crawl_queue_loop
            crawl_task = asyncio.create_task(crawl_queue_loop())
            logger.info("Crawl queue scheduler started")
        except Exception as e:
            logger.warning(f"Crawl scheduler failed to start (non-fatal): {e}")
    else:
        logger.info("Crawl scheduler disabled (set CRAWL_ENABLED=true to enable)")

    logger.info("Diligence backend started")
    yield

    if crawl_task:
        crawl_task.cancel()
        try:
            await crawl_task
        except asyncio.CancelledError:
            pass
    logger.info("Diligence backend shutting down")


app = FastAPI(title="Diligence", version="2.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers after app creation to avoid circular imports
from diligence.routers.auth import router as auth_router
from diligence.routers.onboarding import router as onboarding_router
from diligence.routers.activities import router as activities_router
from diligence.routers.food import router as food_router
from diligence.routers.points import router as points_router, rewards_router
from diligence.routers.integrations import router as integrations_router
from diligence.routers.programs import router as programs_router
from diligence.routers.catalog import router as catalog_router
from diligence.routers.support import router as support_router
from diligence.routers.nutrition import router as nutrition_router
from diligence.routers.meal_plans import router as meal_plans_router
from diligence.routers.ai_chat import router as ai_chat_router

app.include_router(auth_router)
app.include_router(onboarding_router)
app.include_router(activities_router)
app.include_router(food_router)
app.include_router(points_router)
app.include_router(rewards_router)
app.include_router(integrations_router)
app.include_router(catalog_router)
app.include_router(support_router)
app.include_router(programs_router)
app.include_router(nutrition_router)
app.include_router(meal_plans_router)
app.include_router(ai_chat_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "2.0.0"}


# --- Static frontend serving (pip install path) ---
# When running without nginx, serve the pre-built React app directly.
# The frontend/ directory is bundled with the pip package.
_frontend_dir = Path(__file__).parent / "frontend"
if _frontend_dir.is_dir() and (_frontend_dir / "index.html").exists():
    # B2A discovery files
    @app.get("/llms.txt")
    async def llms_txt():
        p = _frontend_dir / "llms.txt"
        if p.exists():
            return FileResponse(p, media_type="text/plain")

    @app.get("/.well-known/{path:path}")
    async def well_known(path: str):
        p = _frontend_dir / ".well-known" / path
        if p.exists():
            media = "text/plain" if path.endswith(".md") else "application/json"
            return FileResponse(p, media_type=media)

    # Static assets (js, css, images)
    app.mount("/assets", StaticFiles(directory=_frontend_dir / "assets"), name="assets")

    # SPA catch-all — must be last
    @app.get("/{path:path}")
    async def spa_catchall(path: str):
        # Don't intercept /api routes (already handled above)
        if path.startswith("api/"):
            return
        file_path = _frontend_dir / path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(_frontend_dir / "index.html")

    logger.info(f"Serving frontend from {_frontend_dir}")


# --- Cross-dialect migrations ---

async def run_migrations():
    """Add missing columns/tables. Works on both PostgreSQL and SQLite."""
    from diligence.database import engine
    from diligence.config import get_settings
    from sqlalchemy import text, inspect as sa_inspect

    settings = get_settings()

    async with engine.begin() as conn:
        # Get table inspector
        def _get_tables_and_columns(connection):
            inspector = sa_inspect(connection)
            tables = inspector.get_table_names()
            columns = {}
            for t in tables:
                columns[t] = [c["name"] for c in inspector.get_columns(t)]
            return tables, columns

        tables, columns = await conn.run_sync(_get_tables_and_columns)

        # v1: Add equipment_list column if missing
        if "user_profiles" in tables and "equipment_list" not in columns.get("user_profiles", []):
            if settings.is_sqlite:
                await conn.execute(text(
                    "ALTER TABLE user_profiles ADD COLUMN equipment_list TEXT DEFAULT '[]'"
                ))
            else:
                await conn.execute(text(
                    "ALTER TABLE user_profiles ADD COLUMN equipment_list JSONB DEFAULT '[]'"
                ))

        # v2: Add catalog columns to programs table
        if "programs" in tables:
            prog_cols = columns.get("programs", [])
            if "catalog_id" not in prog_cols:
                await conn.execute(text(
                    "ALTER TABLE programs ADD COLUMN catalog_id VARCHAR(36)"
                ))
            if "current_week" not in prog_cols:
                await conn.execute(text(
                    "ALTER TABLE programs ADD COLUMN current_week INTEGER DEFAULT 1"
                ))
            if "current_day" not in prog_cols:
                await conn.execute(text(
                    "ALTER TABLE programs ADD COLUMN current_day INTEGER DEFAULT 1"
                ))

        # v2.1: Add week_number to workout_logs
        if "workout_logs" in tables and "week_number" not in columns.get("workout_logs", []):
            await conn.execute(text(
                "ALTER TABLE workout_logs ADD COLUMN week_number INTEGER DEFAULT 1"
            ))

        # v4: Add is_admin to users
        if "users" in tables and "is_admin" not in columns.get("users", []):
            await conn.execute(text(
                "ALTER TABLE users ADD COLUMN is_admin BOOLEAN DEFAULT FALSE"
            ))

        # v4.1: Grant admin to first registered user if none exists
        if "users" in tables and "is_admin" in columns.get("users", []):
            result = await conn.execute(text(
                "SELECT COUNT(*) FROM users WHERE is_admin = TRUE"
            ))
            admin_count = result.scalar()
            if admin_count == 0:
                await conn.execute(text(
                    "UPDATE users SET is_admin = TRUE "
                    "WHERE id = (SELECT id FROM users ORDER BY created_at ASC LIMIT 1)"
                ))

        # v5: integration_configs table — handled by create_all
        # v6: meal plan tables — handled by create_all
        # v7: point rules seeding
        if "point_rules" in tables and "users" in tables:
            for category, points in [
                ("fast_completed", 200),
                ("keto_compliant_day", 100),
                ("meal_plan_followed", 40),
                ("meal_plan_partial", 20),
            ]:
                # Check if any user is missing this rule
                result = await conn.execute(text(
                    "SELECT u.id FROM users u "
                    "WHERE NOT EXISTS ("
                    "  SELECT 1 FROM point_rules pr "
                    "  WHERE pr.user_id = u.id AND pr.category = :cat"
                    ")"
                ), {"cat": category})
                missing_users = result.fetchall()
                for (user_id,) in missing_users:
                    # Use Python uuid for SQLite compatibility
                    import uuid
                    await conn.execute(text(
                        "INSERT INTO point_rules (id, user_id, category, points, unit, is_active) "
                        "VALUES (:id, :uid, :cat, :pts, 'per_event', TRUE)"
                    ), {
                        "id": str(uuid.uuid4()),
                        "uid": str(user_id),
                        "cat": category,
                        "pts": points,
                    })


async def seed_resources():
    """Seed the resource library with curated fitness programs."""
    from diligence.database import async_session
    from diligence.models.resource import Resource
    from sqlalchemy import select

    async with async_session() as db:
        existing = await db.execute(select(Resource).limit(1))
        if existing.scalar_one_or_none():
            return

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
