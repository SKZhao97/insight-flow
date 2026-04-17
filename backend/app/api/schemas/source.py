from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class RSSSourceCreateRequest(BaseModel):
    name: str
    feed_url: HttpUrl
    polling_interval_minutes: int = 60
    tags: list[str] = Field(default_factory=list)


class SourceListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: str
    name: str
    config_json: dict
    status: str
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime
