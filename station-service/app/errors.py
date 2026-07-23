import logging

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppError(Exception):
    def __init__(self, status_code: int, error: str, message: str) -> None:
        self.status_code = status_code
        self.error = error
        self.message = message
        super().__init__(message)


def app_error_handler(_request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error, "message": exc.message},
    )


def _format_validation_message(exc: RequestValidationError) -> str:
    parts: list[str] = []
    for err in exc.errors():
        loc = ".".join(str(part) for part in err.get("loc", ()) if part not in {"body", "query", "path"})
        msg = err.get("msg", "invalid")
        parts.append(f"{loc}: {msg}" if loc else msg)
    return "; ".join(parts) or "Missing or invalid request fields"


def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    message = _format_validation_message(exc)
    logger.debug(
        "VALIDATION_ERROR path=%s method=%s details=%s",
        request.url.path,
        request.method,
        exc.errors(),
    )
    return JSONResponse(
        status_code=400,
        content={"error": "VALIDATION_ERROR", "message": message},
    )
