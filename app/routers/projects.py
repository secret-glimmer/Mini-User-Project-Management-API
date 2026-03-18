import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.database import get_session
from app.exceptions import NotFoundError
from app.schemas import ErrorDetail, ProjectCreate, ProjectRead

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a project",
    description="Create a new project assigned to an existing user.",
    responses={
        404: {"model": ErrorDetail, "description": "Owner user not found"},
    },
)
async def create_project(
    payload: ProjectCreate,
    session: AsyncSession = Depends(get_session),
) -> ProjectRead:
    if not await crud.get_user_by_id(session, payload.owner_id):
        raise NotFoundError("Owner user not found")
    project = await crud.create_project(session, payload)
    return ProjectRead.model_validate(project)


@router.get(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Get project by ID",
    description="Retrieve a single project by its UUID.",
    responses={
        404: {"model": ErrorDetail, "description": "Project not found"},
    },
)
async def get_project(
    project_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
) -> ProjectRead:
    project = await crud.get_project_by_id(session, project_id)
    if not project:
        raise NotFoundError("Project not found")
    return ProjectRead.model_validate(project)
