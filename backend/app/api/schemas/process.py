from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel


class DocumentProcessResult(BaseModel):
    document_id: UUID
    status: str
    quality_status: str
    dedup_status: str
    summary_id: UUID | None = None
    chunk_count: int = 0
    summary_embedding_count: int = 0
    skipped_reason: str | None = None
