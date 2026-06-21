from __future__ import annotations

import asyncio
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fitness-rewards")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Retry DB init — container may start before postgres is fully accepting connections
    for attempt in range(10):
        try:
            from app.database import init_db
            await init_db()
            logger.info("Database tables created successfully")
            break
        except Exception as e:
            logger.warning(f"DB init attempt {attempt + 1}/10 failed: {e}")
            if attempt < 9:
                await asyncio.sleep(3)
            else:
                logger.error("Could not initialize database after 10 attempts — starting without tables")


    # SEC-05: Fail fast if SECRET_KEY not configured
    from app.config import get_settings
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

    # Seed resources (non-fatal if it fails)
    try:
        await seed_resources()
        logger.info("Resource library seeded")
    except Exception as e:
        logger.warning(f"Resource seeding failed (non-fatal): {e}")

    # Start background crawl queue scheduler (gated on CRAWL_ENABLED)
    crawl_task = None
    if _s.crawl_enabled:
        try:
            from app.services.crawl_scheduler import crawl_queue_loop
            crawl_task = asyncio.create_task(crawl_queue_loop())
            logger.info("Crawl queue scheduler started")
        except Exception as e:
            logger.warning(f"Crawl scheduler failed to start (non-fatal): {e}")
    else:
        logger.info("Crawl scheduler disabled (set CRAWL_ENABLED=true to enable)")

    logger.info("Fitness Rewards backend started")
    yield

    # Shutdown
    if crawl_task:
        crawl_task.cancel()
        try:
            await crawl_task
        except asyncio.CancelledError:
            pass
    logger.info("Fitness Rewards backend shutting down")


app = FastAPI(title="Fitness Rewards", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False  # Bearer tokens don't need credentials mode,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import routers after app creation to avoid circular imports
from app.routers.auth import router as auth_router
from app.routers.onboarding import router as onboarding_router
from app.routers.activities import router as activities_router
from app.routers.food import router as food_router
from app.routers.points import router as points_router, rewards_router
from app.routers.integrations import router as integrations_router
from app.routers.programs import router as programs_router
from app.routers.catalog import router as catalog_router
from app.routers.support import router as support_router
from app.routers.nutrition import router as nutrition_router
from app.routers.meal_plans import router as meal_plans_router

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


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}



async def run_migrations():
    """Add missing columns to existing tables (lightweight schema migration)."""
    from app.database import engine
    from sqlalchemy import text

    async with engine.begin() as conn:
        # v1: Add equipment_list JSONB column if missing
        await conn.execute(text("""
            DO $$ BEGIN
                ALTER TABLE user_profiles ADD COLUMN IF NOT EXISTS equipment_list JSONB DEFAULT '[]';
            EXCEPTION WHEN undefined_table THEN NULL;
            END $$;
        """))

        # v2: Add catalog columns to programs table
        await conn.execute(text("""
            DO $$ BEGIN
                ALTER TABLE programs ADD COLUMN IF NOT EXISTS catalog_id UUID REFERENCES program_catalog(id);
                ALTER TABLE programs ADD COLUMN IF NOT EXISTS current_week INTEGER DEFAULT 1;
                ALTER TABLE programs ADD COLUMN IF NOT EXISTS current_day INTEGER DEFAULT 1;
            EXCEPTION WHEN undefined_table THEN NULL;
            END $$;
        """))

        # v2.1: Add week_number to workout_logs for template rotation tracking
        await conn.execute(text("""
            DO $$ BEGIN
                ALTER TABLE workout_logs ADD COLUMN IF NOT EXISTS week_number INTEGER NOT NULL DEFAULT 1;
            EXCEPTION WHEN undefined_table THEN NULL;
            END $$;
        """))

        # v3: Seed keto point rules (fast_completed, keto_day, meal_logged)
        # NOTE: Keto rules below are from v2. v3+ migrations (is_admin, integration_configs,
        # meal plans) are added after this block.
        await conn.execute(text("""
            DO $$ BEGIN
                INSERT INTO point_rules (id, user_id, category, points, unit, is_active)
                SELECT gen_random_uuid(), u.id, 'fast_completed', 200, 'per_event', TRUE
                FROM users u
                WHERE NOT EXISTS (
                    SELECT 1 FROM point_rules pr
                    WHERE pr.user_id = u.id AND pr.category = 'fast_completed'
                );
                INSERT INTO point_rules (id, user_id, category, points, unit, is_active)
                SELECT gen_random_uuid(), u.id, 'keto_compliant_day', 100, 'per_event', TRUE
                FROM users u
                WHERE NOT EXISTS (
                    SELECT 1 FROM point_rules pr
                    WHERE pr.user_id = u.id AND pr.category = 'keto_compliant_day'
                );
            EXCEPTION WHEN undefined_table THEN NULL;
            END $$;
        """))

        # v4: Add is_admin column to users
        await conn.execute(text("""
            DO $$ BEGIN
                ALTER TABLE users ADD COLUMN IF NOT EXISTS is_admin BOOLEAN DEFAULT FALSE;
            EXCEPTION WHEN undefined_table THEN NULL;
            END $$;
        """))

        # v4.1: Grant admin to first registered user if no admin exists
        await conn.execute(text("""
            DO $$ BEGIN
                IF NOT EXISTS (SELECT 1 FROM users WHERE is_admin = TRUE) THEN
                    UPDATE users SET is_admin = TRUE
                    WHERE id = (SELECT id FROM users ORDER BY created_at ASC LIMIT 1);
                END IF;
            EXCEPTION WHEN undefined_table THEN NULL;
            WHEN undefined_column THEN NULL;
            END $$;
        """))

        # v5: Create integration_configs table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS integration_configs (
                id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id         UUID NOT NULL REFERENCES users(id),
                provider        VARCHAR(50) NOT NULL,
                config_key      VARCHAR(100) NOT NULL,
                config_value    TEXT NOT NULL,
                created_at      TIMESTAMPTZ DEFAULT NOW(),
                updated_at      TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(user_id, provider, config_key)
            );
        """))

        # v6: Create meal plan tables
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS meal_plans (
                id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id         UUID NOT NULL REFERENCES users(id),
                name            VARCHAR(200) NOT NULL,
                diet_type       VARCHAR(50),
                daily_calories  INTEGER,
                daily_protein_g INTEGER,
                daily_carbs_g   INTEGER,
                daily_fat_g     INTEGER,
                restrictions    JSONB DEFAULT '[]',
                duration_days   INTEGER NOT NULL,
                start_date      DATE NOT NULL,
                status          VARCHAR(20) DEFAULT 'active',
                created_at      TIMESTAMPTZ DEFAULT NOW()
            );
        """))

        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS meal_plan_items (
                id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                plan_id         UUID NOT NULL REFERENCES meal_plans(id) ON DELETE CASCADE,
                day_number      INTEGER NOT NULL,
                meal_type       VARCHAR(20) NOT NULL,
                food_name       VARCHAR(300) NOT NULL,
                description     TEXT,
                calories        INTEGER,
                protein_g       DECIMAL(6,1),
                carbs_g         DECIMAL(6,1),
                fat_g           DECIMAL(6,1),
                fiber_g         DECIMAL(6,1),
                serving_size    VARCHAR(100),
                sort_order      INTEGER DEFAULT 0,
                created_at      TIMESTAMPTZ DEFAULT NOW()
            );
        """))

        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS meal_compliance (
                id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id         UUID NOT NULL REFERENCES users(id),
                plan_id         UUID NOT NULL REFERENCES meal_plans(id),
                plan_item_id    UUID,
                compliance_date DATE NOT NULL,
                status          VARCHAR(20) NOT NULL,
                substitution    TEXT,
                food_log_id     UUID,
                created_at      TIMESTAMPTZ DEFAULT NOW()
            );
        """))

        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_meal_plan_items_day ON meal_plan_items(plan_id, day_number);
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_meal_compliance_date ON meal_compliance(user_id, compliance_date);
        """))

        # v7: Seed meal plan point rules
        await conn.execute(text("""
            DO $$ BEGIN
                INSERT INTO point_rules (id, user_id, category, points, unit, is_active)
                SELECT gen_random_uuid(), u.id, 'meal_plan_followed', 40, 'per_event', TRUE
                FROM users u
                WHERE NOT EXISTS (
                    SELECT 1 FROM point_rules pr
                    WHERE pr.user_id = u.id AND pr.category = 'meal_plan_followed'
                );
                INSERT INTO point_rules (id, user_id, category, points, unit, is_active)
                SELECT gen_random_uuid(), u.id, 'meal_plan_partial', 20, 'per_event', TRUE
                FROM users u
                WHERE NOT EXISTS (
                    SELECT 1 FROM point_rules pr
                    WHERE pr.user_id = u.id AND pr.category = 'meal_plan_partial'
                );
            EXCEPTION WHEN undefined_table THEN NULL;
            END $$;
        """))


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
