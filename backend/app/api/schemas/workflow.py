from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class WeeklyWorkflowRunRequest(BaseModel):
    """Request payload for starting one weekly report workflow run."""

    week_start: datetime
    week_end: datetime
    input_document_ids: list[UUID] = Field(default_factory=list)


class WeeklyWorkflowRunResponse(BaseModel):
    """Compact workflow snapshot returned by run/resume endpoints."""

    workflow_run_id: UUID
    status: str
    human_edit_status: str | None = None
    report_id: UUID | None = None
    review_decision: str | None = None
    exported_markdown_path: str | None = None
