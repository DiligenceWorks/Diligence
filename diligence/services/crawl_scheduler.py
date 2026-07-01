"""Crawl queue scheduler — processes jobs respecting priority and time constraints."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from diligence.database import async_session
from diligence.models.catalog import CrawlQueue
from diligence.services.program_research import process_crawl_job

logger = logging.getLogger(__name__)

# ICT = UTC+7. Off-peak: 22:00-06:00 ICT = 15:00-23:00 UTC
OFFPEAK_START_UTC = 15  # 22:00 ICT
OFFPEAK_END_UTC = 23    # 06:00 ICT


def is_offpeak() -> bool:
    """Check if current time is off-peak (22:00-06:00 ICT)."""
    hour = datetime.now(timezone.utc).hour
    return hour >= OFFPEAK_START_UTC or hour < OFFPEAK_END_UTC


def is_weekend() -> bool:
    """Check if today is Saturday (5) or Sunday (6)."""
    return datetime.now(timezone.utc).weekday() >= 5


async def has_higher_priority_jobs(db: AsyncSession) -> bool:
    """Check if any HIGH or MEDIUM priority jobs are pending."""
    result = await db.execute(
        select(func.count(CrawlQueue.id)).where(
            CrawlQueue.priority.in_(["high", "medium"]),
            CrawlQueue.status == "pending",
        )
    )
    return (result.scalar() or 0) > 0


async def get_next_pending_job(db: AsyncSession) -> CrawlQueue | None:
    """Get the oldest pending LOW priority crawl job."""
    result = await db.execute(
        select(CrawlQueue)
        .where(CrawlQueue.status == "pending", CrawlQueue.priority == "low")
        .order_by(CrawlQueue.created_at.asc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def run_queue_cycle() -> None:
    """Process one job from the queue if conditions are met."""
    # Only run during off-peak or weekends
    if not is_offpeak() and not is_weekend():
        return

    async with async_session() as db:
        try:
            # Defer to higher priority work
            if await has_higher_priority_jobs(db):
                logger.debug("Higher priority jobs pending — skipping fitness crawl")
                return

            job = await get_next_pending_job(db)
            if not job:
                return

            logger.info(f"Processing crawl job {job.id}: {job.search_query}")
            await process_crawl_job(db, job)
            await db.commit()
            logger.info(f"Crawl job {job.id} completed with status: {job.status}")

        except Exception as e:
            logger.error(f"Crawl queue cycle error: {e}")
            await db.rollback()


async def crawl_queue_loop() -> None:
    """Background loop — checks queue every 5 minutes."""
    logger.info("Crawl queue scheduler started")
    while True:
        try:
            await run_queue_cycle()
        except Exception as e:
            logger.error(f"Crawl queue loop error: {e}")
        await asyncio.sleep(300)  # 5 minutes
