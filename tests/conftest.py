from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.database import get_session, get_session_factory, reset_engine

test_engine = reset_engine(
    "sqlite+aiosqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(test_engine.sync_engine, "connect")
def _enable_sqlite_fks(dbapi_connection, _connection_record):
    dbapi_connection.execute("PRAGMA foreign_keys=ON")


async def _override_get_session() -> AsyncGenerator[AsyncSession, None]:
    async with get_session_factory()() as session:
        yield session


@pytest_asyncio.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    from app.main import app

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    app.dependency_overrides[get_session] = _override_get_session
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
    app.dependency_overrides.clear()

    async with test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)
