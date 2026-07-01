"""Program research service — crawl fitness programs and extract structured data via Groq."""
from __future__ import annotations

import json
import re
import subprocess
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from diligence.models.catalog import ProgramCatalog, CatalogWorkout, CrawlQueue
from diligence.config import settings


# ── Known program sources (skip search for these) ──────────────────────────

KNOWN_SOURCES: dict[str, list[str]] = {
    "stronglifts 5x5": ["https://stronglifts.com/5x5/"],
    "stronglifts": ["https://stronglifts.com/5x5/"],
    "starting strength": ["https://startingstrength.com/get-started/programs"],
    "couch to 5k": [
        "https://www.nhs.uk/live-well/exercise/running-and-aerobic-exercises/get-running-with-couch-to-5k/"
    ],
    "c25k": [
        "https://www.nhs.uk/live-well/exercise/running-and-aerobic-exercises/get-running-with-couch-to-5k/"
    ],
    "greyskull lp": ["https://physiqz.com/powerlifting-programs/greyskull-lp-best-powerlifting-routine-for-beginners/"],
    "5/3/1": ["https://www.jimwendler.com/blogs/jimwendler-com/101065094-5-3-1-for-a-beginner"],
    "wendler 531": ["https://www.jimwendler.com/blogs/jimwendler-com/101065094-5-3-1-for-a-beginner"],
    "push pull legs": ["https://www.muscleandstrength.com/workouts/6-day-push-pull-legs-planet-fitness-workout"],
    "ppl": ["https://www.muscleandstrength.com/workouts/6-day-push-pull-legs-planet-fitness-workout"],
    "phul": ["https://www.muscleandstrength.com/workouts/phul-workout"],
    "power hypertrophy upper lower": ["https://www.muscleandstrength.com/workouts/phul-workout"],
    "darebee foundation": ["https://darebee.com/programs/foundation-light-program.html"],
    "foundation light": ["https://darebee.com/programs/foundation-light-program.html"],
    "darebee 30 days of change": ["https://darebee.com/programs/30-days-of-change.html"],
}


# ── Groq extraction prompt ─────────────────────────────────────────────────

EXTRACTION_PROMPT = """You are a fitness program parser. Extract the workout program from the content below into structured JSON.

Return ONLY valid JSON matching this exact schema — no markdown fences, no explanation:

{
  "name": "Program Name",
  "description": "Brief 1-2 sentence description",
  "duration_weeks": 12,
  "frequency_per_week": 3,
  "difficulty": "beginner",
  "category": "strength",
  "equipment": ["barbell", "squat rack", "bench"],
  "progression_rules": "Human-readable progression description. E.g. 'Add 2.5kg per session on all lifts. If you fail a weight 3 sessions in a row, deload 10%.'",
  "workouts": [
    {
      "week": 1,
      "day": 1,
      "name": "Workout A",
      "rest_day": false,
      "exercises": [
        {
          "name": "Squat",
          "sets": 5,
          "reps": 5,
          "weight_instruction": "Start with empty bar (20kg), add 2.5kg each session",
          "rest_seconds": 180,
          "notes": "Below parallel"
        }
      ],
      "notes": null
    }
  ]
}

Rules:
- difficulty must be one of: beginner, intermediate, advanced
- category must be one of: strength, cardio, flexibility, hybrid
- For alternating programs (A/B/A rotation), output the minimum unique weeks needed to show the pattern. Explain the rotation in progression_rules.
- If a day is a rest day, set rest_day: true and exercises: []
- weight_instruction should be specific if the source provides guidance, otherwise "Use appropriate weight"
- rest_seconds: use the source value, or 60-90 for hypertrophy, 180-300 for strength, 30-60 for cardio
- Include ALL exercises mentioned for each workout day
"""


def slugify(name: str) -> str:
    """Convert program name to URL-safe slug."""
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"[\s-]+", "-", s)
    return s[:200]


def find_urls_for_program(query: str) -> list[str]:
    """Look up known URLs or return empty list for unknown programs."""
    q = query.lower().strip()
    for key, urls in KNOWN_SOURCES.items():
        if key in q or q in key:
            return urls
    return []


async def crawl_url(url: str) -> str:
    """Call ttp-crawler on subo to fetch a URL as markdown."""
    proc = subprocess.run(
        [
            "python3", "/home/claude/ttp-crawler/crawl.py",
            "fetch", url, "--output", "md",
        ],
        capture_output=True,
        text=True,
        timeout=120,
        cwd="/home/claude/ttp-crawler",
    )
    if proc.returncode != 0:
        raise RuntimeError(f"Crawl failed: {proc.stderr[:500]}")
    return proc.stdout


async def extract_with_groq(crawled_content: str) -> dict[str, Any]:
    """Send crawled markdown to Groq for structured extraction."""
    # Truncate to fit context — Llama 3.3 70B has 128k context but we keep it reasonable
    content = crawled_content[:15000]

    async with httpx.AsyncClient(timeout=90.0) as client:
        resp = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.groq_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": [
                    {"role": "system", "content": EXTRACTION_PROMPT},
                    {"role": "user", "content": content},
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.1,
                "max_tokens": 8000,
            },
        )
        resp.raise_for_status()
        data = resp.json()
        raw = data["choices"][0]["message"]["content"]
        return json.loads(raw)


def validate_extraction(data: dict) -> tuple[bool, str]:
    """Basic validation of Groq extraction output."""
    required = ["name", "workouts"]
    for field in required:
        if field not in data:
            return False, f"Missing required field: {field}"

    if not isinstance(data.get("workouts"), list) or len(data["workouts"]) == 0:
        return False, "No workouts extracted"

    for i, w in enumerate(data["workouts"]):
        if not w.get("rest_day", False) and not w.get("exercises"):
            return False, f"Workout {i + 1} has no exercises and is not a rest day"

    return True, "OK"


async def populate_catalog_from_extraction(
    db: AsyncSession, catalog: ProgramCatalog, data: dict
) -> None:
    """Write validated extraction data into catalog + catalog_workouts."""
    catalog.name = data.get("name", catalog.name)
    catalog.description = data.get("description")
    catalog.duration_weeks = data.get("duration_weeks")
    catalog.frequency_per_week = data.get("frequency_per_week")
    catalog.equipment = data.get("equipment", [])
    catalog.difficulty = data.get("difficulty")
    catalog.category = data.get("category")
    catalog.progression_rules = data.get("progression_rules")
    catalog.structured_data = data
    catalog.crawl_status = "ready"
    catalog.crawled_at = datetime.now(timezone.utc)

    for w in data.get("workouts", []):
        workout = CatalogWorkout(
            catalog_id=catalog.id,
            week_number=w.get("week", 1),
            day_number=w.get("day", 1),
            workout_name=w.get("name"),
            exercises=w.get("exercises", []),
            notes=w.get("notes"),
            rest_day=w.get("rest_day", False),
        )
        db.add(workout)

    await db.flush()


async def process_crawl_job(db: AsyncSession, job: CrawlQueue) -> None:
    """Execute a single crawl queue job end-to-end."""
    job.status = "running"
    job.started_at = datetime.now(timezone.utc)
    await db.flush()

    catalog = None
    if job.catalog_id:
        result = await db.execute(
            select(ProgramCatalog).where(ProgramCatalog.id == job.catalog_id)
        )
        catalog = result.scalar_one_or_none()

    try:
        # Step 1: Determine URLs to crawl
        urls = job.urls_to_crawl if job.urls_to_crawl else find_urls_for_program(job.search_query)
        if not urls:
            raise ValueError(
                f"No known sources for '{job.search_query}'. "
                "Add URLs manually or extend KNOWN_SOURCES."
            )

        # Step 2: Crawl
        crawled_parts = []
        for url in urls:
            try:
                content = await crawl_url(url)
                if len(content.strip()) > 200:  # skip near-empty crawls
                    crawled_parts.append(content)
            except Exception as e:
                crawled_parts.append(f"[Crawl error for {url}: {e}]")

        if not crawled_parts:
            raise ValueError("All crawl attempts returned empty content")

        combined = "\n\n---\n\n".join(crawled_parts)
        job.crawled_content = combined[:50000]  # store for debugging, cap at 50KB

        # Step 3: Extract via Groq
        if catalog:
            catalog.crawl_status = "extracting"
            await db.flush()

        extracted = await extract_with_groq(combined)

        # Step 4: Validate
        valid, reason = validate_extraction(extracted)
        if not valid:
            raise ValueError(f"Extraction validation failed: {reason}")

        # Step 5: Populate catalog
        if catalog:
            await populate_catalog_from_extraction(db, catalog, extracted)

        job.status = "done"
        job.completed_at = datetime.now(timezone.utc)

    except Exception as e:
        job.status = "failed"
        job.error = str(e)[:2000]
        job.completed_at = datetime.now(timezone.utc)
        if catalog:
            catalog.crawl_status = "failed"
            catalog.crawl_error = str(e)[:2000]

    await db.flush()
