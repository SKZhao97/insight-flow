from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class URLIngestRequest(BaseModel):
    url: HttpUrl
    source_id: UUID | None = None
    title_hint: str | None = None


class ManualTextIngestRequest(BaseModel):
    title: str
    content: str = Field(min_length=1)
    source_id: UUID | None = None
    author: str | None = None
    language: str | None = None


class DocumentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    source_id: UUID | None
    ingest_type: str
    url: str | None
    canonical_url: str | None
    title: str
    author: str | None
    published_at: datetime | None
    language: str | None
    content_hash: str
    extraction_method: str
    quality_status: str
    dedup_status: str
    status: str
    created_at: datetime
    updated_at: datetime
