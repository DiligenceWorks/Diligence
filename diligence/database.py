from __future__ import annotations

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from diligence.config import get_settings

settings = get_settings()

# Build engine with dialect-appropriate settings
_engine_kwargs: dict = {"echo": False}
if not settings.is_sqlite:
    # PostgreSQL — connection pooling
    _engine_kwargs.update(pool_size=5, max_overflow=10)

engine = create_async_engine(settings.effective_database_url, **_engine_kwargs)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    # Import all models so their tables are registered on Base.metadata
    import diligence.models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
