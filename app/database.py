import asyncio
import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlmodel import SQLModel

logger = logging.getLogger(__name__)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None

_MAX_STARTUP_RETRIES = 5
_RETRY_BASE_DELAY = 2


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        from app.config import get_settings

        s = get_settings()
        _engine = create_async_engine(
            s.database_url,
            echo=False,
            pool_size=s.db_pool_size,
            max_overflow=s.db_max_overflow,
            pool_recycle=s.db_pool_recycle,
            pool_pre_ping=True,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


def reset_engine(url: str, **kwargs) -> AsyncEngine:
    """Replace the global engine (used by tests to swap in SQLite)."""
    global _engine, _session_factory
    _engine = create_async_engine(url, **kwargs)
    _session_factory = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return _engine


async def create_db_and_tables() -> None:
    for attempt in range(1, _MAX_STARTUP_RETRIES + 1):
        try:
            async with get_engine().begin() as conn:
                await conn.run_sync(SQLModel.metadata.create_all)
            logger.info("Database tables ready (attempt %d)", attempt)
            return
        except Exception:
            if attempt == _MAX_STARTUP_RETRIES:
                logger.error("Failed to connect after %d attempts", attempt)
                raise
            delay = _RETRY_BASE_DELAY**attempt
            logger.warning(
                "DB not ready (attempt %d/%d), retrying in %ds …",
                attempt,
                _MAX_STARTUP_RETRIES,
                delay,
            )
            await asyncio.sleep(delay)


async def dispose_engine() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Database engine disposed")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with get_session_factory()() as session:
        yield session
