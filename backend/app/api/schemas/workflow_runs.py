from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class WorkflowRunListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workflow_type: str
    status: str
    week_start: datetime | None
    week_end: datetime | None
    retry_count: int
    started_at: datetime
    finished_at: datetime | None
    created_at: datetime
    updated_at: datetime
