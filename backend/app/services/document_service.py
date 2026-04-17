from __future__ import annotations

import hashlib
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.schemas.document import ManualTextIngestRequest, URLIngestRequest
from app.core.logging import get_logger
from app.db.enums import (
    DocumentDedupStatus,
    DocumentExtractionMethod,
    DocumentIngestType,
    DocumentQualityStatus,
    DocumentStatus,
)
from app.db.models.document import Document
from app.db.models.source import Source


logger = get_logger(__name__)


class SourceNotFoundError(ValueError):
    pass


class DocumentConflictError(ValueError):
    pass


def _canonicalize_url(raw_url: str) -> str:
    parts = urlsplit(raw_url.strip())
    normalized_path = parts.path or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), normalized_path, parts.query, ""))


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _ensure_source_exists(db: Session, source_id) -> None:
    if source_id is None:
        return

    source = db.get(Source, source_id)
    if source is None:
        raise SourceNotFoundError(f"source {source_id} not found")


def list_documents(db: Session) -> list[Document]:
    stmt = select(Document).order_by(Document.created_at.desc())
    return list(db.scalars(stmt).all())


def create_url_document(db: Session, payload: URLIngestRequest) -> Document:
    _ensure_source_exists(db, payload.source_id)
    canonical_url = _canonicalize_url(str(payload.url))
    title = payload.title_hint.strip() if payload.title_hint else canonical_url

    document = Document(
        source_id=payload.source_id,
        ingest_type=DocumentIngestType.URL.value,
        url=str(payload.url),
        canonical_url=canonical_url,
        title=title,
        content_hash=_hash_text(f"url:{canonical_url}"),
        extraction_method=DocumentExtractionMethod.LOCAL.value,
        quality_status=DocumentQualityStatus.PENDING.value,
        dedup_status=DocumentDedupStatus.PENDING.value,
        status=DocumentStatus.INGESTED.value,
    )
    db.add(document)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DocumentConflictError(
            f"document with canonical_url {canonical_url} already exists"
        ) from exc
    db.refresh(document)

    logger.info(
        "document.ingested document_id=%s ingest_type=%s canonical_url=%s source_id=%s",
        document.id,
        document.ingest_type,
        document.canonical_url,
        document.source_id,
    )
    return document


def create_manual_text_document(db: Session, payload: ManualTextIngestRequest) -> Document:
    _ensure_source_exists(db, payload.source_id)
    cleaned_content = payload.content.strip()
    document = Document(
        source_id=payload.source_id,
        ingest_type=DocumentIngestType.MANUAL_TEXT.value,
        title=payload.title.strip(),
        author=payload.author.strip() if payload.author else None,
        language=payload.language,
        raw_content=cleaned_content,
        cleaned_content=cleaned_content,
        content_hash=_hash_text(f"manual:{cleaned_content}"),
        extraction_method=DocumentExtractionMethod.LOCAL.value,
        quality_status=DocumentQualityStatus.PENDING.value,
        dedup_status=DocumentDedupStatus.PENDING.value,
        status=DocumentStatus.INGESTED.value,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    logger.info(
        "document.ingested document_id=%s ingest_type=%s source_id=%s content_length=%s",
        document.id,
        document.ingest_type,
        document.source_id,
        len(cleaned_content),
    )
    return document
