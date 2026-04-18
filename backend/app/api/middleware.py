from __future__ import annotations

import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.logging import bind_request_context, clear_request_context, get_logger


logger = get_logger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        trace_id = request.headers.get("X-Trace-ID") or request_id
        started_at = time.perf_counter()

        request.state.request_id = request_id
        request.state.trace_id = trace_id
        bind_request_context(request_id=request_id, trace_id=trace_id)

        logger.info("request.started method=%s path=%s", request.method, request.url.path)

        try:
            response = await call_next(request)
        except Exception:
            logger.exception("request.failed method=%s path=%s", request.method, request.url.path)
            raise
        else:
            elapsed_ms = (time.perf_counter() - started_at) * 1000
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Trace-ID"] = trace_id

            logger.info(
                "request.completed method=%s path=%s status_code=%s elapsed_ms=%.2f",
                request.method,
                request.url.path,
                response.status_code,
                elapsed_ms,
            )
            return response
        finally:
            clear_request_context()
