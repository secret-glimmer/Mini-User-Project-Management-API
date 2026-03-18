import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import create_db_and_tables, dispose_engine, get_session
from app.exceptions import register_exception_handlers
from app.routers import projects, users

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    await create_db_and_tables()
    logger.info("Application startup complete")
    yield
    await dispose_engine()
    logger.info("Application shutdown complete")


app = FastAPI(
    title="Mini User & Project Management API",
    description=(
        "REST API for managing users and their projects. "
        "Supports CRUD operations with pagination and cascade deletes."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

register_exception_handlers(app)
app.include_router(users.router)
app.include_router(projects.router)


@app.get(
    "/health",
    tags=["System"],
    summary="Health check",
    description="Verify the API and database are reachable.",
    status_code=status.HTTP_200_OK,
)
async def health_check(
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    await session.execute(text("SELECT 1"))
    return {"status": "healthy"}
