import logging
import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ConflictError, NotFoundError
from app.models import Project, User
from app.schemas import ProjectCreate, UserCreate

logger = logging.getLogger(__name__)


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, payload: UserCreate) -> User:
    user = User(name=payload.name, email=str(payload.email))
    session.add(user)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        logger.warning("Duplicate email caught by DB constraint: %s", payload.email)
        raise ConflictError("A user with this email already exists")
    await session.refresh(user)
    return user


async def get_user_by_id(session: AsyncSession, user_id: uuid.UUID) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def list_users(
    session: AsyncSession, *, limit: int, offset: int
) -> list[User]:
    result = await session.execute(
        select(User).order_by(User.created_at).offset(offset).limit(limit)
    )
    return list(result.scalars().all())


async def delete_user(session: AsyncSession, user: User) -> None:
    await session.delete(user)
    await session.commit()


async def create_project(session: AsyncSession, payload: ProjectCreate) -> Project:
    project = Project(
        title=payload.title,
        description=payload.description,
        owner_id=payload.owner_id,
    )
    session.add(project)
    try:
        await session.commit()
    except IntegrityError:
        await session.rollback()
        logger.warning("FK violation creating project for owner %s", payload.owner_id)
        raise NotFoundError("Owner user not found")
    await session.refresh(project)
    return project


async def get_project_by_id(
    session: AsyncSession, project_id: uuid.UUID
) -> Project | None:
    result = await session.execute(select(Project).where(Project.id == project_id))
    return result.scalar_one_or_none()


async def list_projects_by_owner(
    session: AsyncSession, owner_id: uuid.UUID
) -> list[Project]:
    result = await session.execute(
        select(Project)
        .where(Project.owner_id == owner_id)
        .order_by(Project.created_at)
    )
    return list(result.scalars().all())
