import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.database import get_session
from app.exceptions import ConflictError, NotFoundError
from app.schemas import ErrorDetail, ProjectRead, UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["Users"])


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a user",
    description="Create a new user with a unique email address.",
    responses={
        409: {"model": ErrorDetail, "description": "Email already registered"},
    },
)
async def create_user(
    payload: UserCreate,
    session: AsyncSession = Depends(get_session),
) -> UserRead:
    if await crud.get_user_by_email(session, str(payload.email)):
        raise ConflictError("A user with this email already exists")
    user = await crud.create_user(session, payload)
    return UserRead.model_validate(user)


@router.get(
    "",
    response_model=list[UserRead],
    summary="List users",
    description="Retrieve a paginated list of users ordered by creation date.",
)
async def list_users(
    limit: int = Query(default=10, ge=1, le=100, description="Max items to return"),
    offset: int = Query(default=0, ge=0, description="Items to skip"),
    session: AsyncSession = Depends(get_session),
) -> list[UserRead]:
    users = await crud.list_users(session, limit=limit, offset=offset)
    return [UserRead.model_validate(u) for u in users]


@router.get(
    "/{user_id}",
    response_model=UserRead,
    summary="Get user by ID",
    description="Retrieve a single user by their UUID.",
    responses={
        404: {"model": ErrorDetail, "description": "User not found"},
    },
)
async def get_user(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> UserRead:
    user = await crud.get_user_by_id(session, user_id)
    if not user:
        raise NotFoundError("User not found")
    return UserRead.model_validate(user)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
    description="Delete a user and cascade-delete all their projects.",
    responses={
        404: {"model": ErrorDetail, "description": "User not found"},
    },
)
async def delete_user(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> None:
    user = await crud.get_user_by_id(session, user_id)
    if not user:
        raise NotFoundError("User not found")
    await crud.delete_user(session, user)


@router.get(
    "/{user_id}/projects",
    response_model=list[ProjectRead],
    tags=["Projects"],
    summary="List user projects",
    description="Retrieve all projects owned by a specific user.",
    responses={
        404: {"model": ErrorDetail, "description": "User not found"},
    },
)
async def list_user_projects(
    user_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> list[ProjectRead]:
    user = await crud.get_user_by_id(session, user_id)
    if not user:
        raise NotFoundError("User not found")
    projects = await crud.list_projects_by_owner(session, owner_id=user_id)
    return [ProjectRead.model_validate(p) for p in projects]
