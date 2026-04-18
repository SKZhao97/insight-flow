from __future__ import annotations

"""Centralized API exception handlers for consistent error responses."""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import get_logger


logger = get_logger(__name__)


def _request_context_payload(request: Request) -> dict[str, str]:
    """
    Extract trace identifiers from request state so clients can correlate
    failures with application logs.
    """

    return {
        "request_id": getattr(request.state, "request_id", "-"),
        "trace_id": getattr(request.state, "trace_id", "-"),
    }


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Return a structured 422 payload with trace identifiers."""

    context = _request_context_payload(request)
    logger.warning(
        "request.validation_failed method=%s path=%s request_id=%s trace_id=%s error_count=%s",
        request.method,
        request.url.path,
        context["request_id"],
        context["trace_id"],
        len(exc.errors()),
    )
    return JSONResponse(
        status_code=422,
        content={
            "detail": "request_validation_failed",
            "errors": exc.errors(),
            **context,
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a stable 500 payload and preserve the correlation identifiers."""

    context = _request_context_payload(request)
    logger.exception(
        "request.unhandled_exception method=%s path=%s request_id=%s trace_id=%s error_code=%s",
        request.method,
        request.url.path,
        context["request_id"],
        context["trace_id"],
        exc.__class__.__name__,
    )
    return JSONResponse(
        status_code=500,
        content={
            "detail": "internal_server_error",
            **context,
        },
    )
