from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ReportListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: str
    title: str
    window_start: datetime
    window_end: datetime
    status: str
    version: int
    generated_by_run_id: UUID | None
    created_at: datetime
    updated_at: datetime


class ReportItemView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    summary_id: UUID
    document_id: UUID
    cluster_id: UUID | None
    source_url: str
    item_type: str
    position: int
    created_at: datetime


class ReportTraceItem(BaseModel):
    """Explicit citation-trace item for report provenance inspection."""

    id: UUID
    position: int
    item_type: str
    source_url: str
    cluster_id: UUID | None
    document_id: UUID
    document_title: str
    summary_id: UUID
    summary_text: str


class ReportTraceResponse(BaseModel):
    """Trace payload that links report output back to stored evidence records."""

    report_id: UUID
    title: str
    generated_by_run_id: UUID | None
    items: list[ReportTraceItem]


class ReportDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: str
    title: str
    window_start: datetime
    window_end: datetime
    content_md: str
    status: str
    version: int
    generated_by_run_id: UUID | None
    created_at: datetime
    updated_at: datetime
    items: list[ReportItemView]
