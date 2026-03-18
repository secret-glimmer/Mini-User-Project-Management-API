import logging

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from starlette.requests import Request

logger = logging.getLogger(__name__)


class NotFoundError(Exception):
    """Raised when a requested entity does not exist."""

    def __init__(self, detail: str = "Resource not found"):
        self.detail = detail
        super().__init__(detail)


class ConflictError(Exception):
    """Raised on uniqueness / business-rule conflicts."""

    def __init__(self, detail: str = "Conflict"):
        self.detail = detail
        super().__init__(detail)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def _not_found(request: Request, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"detail": exc.detail},
        )

    @app.exception_handler(ConflictError)
    async def _conflict(request: Request, exc: ConflictError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": exc.detail},
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )
