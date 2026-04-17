from __future__ import annotations

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.models.document import Document, DocumentChunk
from app.services.embedding_service import EMBEDDING_MODEL_NAME, embed_text, log_embedding_created


logger = get_logger(__name__)

MAX_CHUNK_LENGTH = 700
OVERLAP_LENGTH = 120


def _split_into_chunks(text: str) -> list[str]:
    if len(text) <= MAX_CHUNK_LENGTH:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + MAX_CHUNK_LENGTH, len(text))
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(0, end - OVERLAP_LENGTH)
    return [chunk for chunk in chunks if chunk]


def rebuild_document_chunks(db: Session, document: Document) -> list[DocumentChunk]:
    content = (document.cleaned_content or "").strip()
    chunks = _split_into_chunks(content)

    db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document.id))
    db.flush()

    records: list[DocumentChunk] = []
    for idx, chunk_text in enumerate(chunks):
        chunk = DocumentChunk(
            document_id=document.id,
            chunk_index=idx,
            chunk_text=chunk_text,
            token_count=max(1, len(chunk_text) // 4),
            embedding_model=EMBEDDING_MODEL_NAME,
            embedding=embed_text(chunk_text),
        )
        db.add(chunk)
        records.append(chunk)

    db.commit()
    for record in records:
        db.refresh(record)
        log_embedding_created("document_chunk", record.id, "chunk_text")

    logger.info(
        "document.chunks.rebuilt document_id=%s chunk_count=%s embedding_model=%s",
        document.id,
        len(records),
        EMBEDDING_MODEL_NAME,
    )
    return records
