from __future__ import annotations

from fastapi import Request


def get_request_ids(request: Request) -> tuple[str, str]:
    return request.state.request_id, request.state.trace_id
