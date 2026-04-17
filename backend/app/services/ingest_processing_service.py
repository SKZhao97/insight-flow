from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.enums import (
    DocumentDedupStatus,
    DocumentIngestType,
    DocumentQualityStatus,
    DocumentStatus,
)
from app.db.models.document import Document
from app.db.models.summary import Summary
from app.services.analysis_service import upsert_document_summary
from app.services.chunk_service import rebuild_document_chunks
from app.services.dedup_service import assess_document_dedup
from app.services.fetch_service import DocumentFetchError, fetch_document_content
from app.services.normalization_service import (
    DocumentNormalizationError,
    compute_content_hash,
    normalize_text,
)
from app.services.quality_service import evaluate_document_quality
from app.services.summary_embedding_service import upsert_summary_embedding


logger = get_logger(__name__)


class DocumentNotFoundError(ValueError):
    pass


@dataclass(slots=True)
class DocumentProcessingResult:
    document: Document
    summary: Summary | None = None
    chunk_count: int = 0
    summary_embedding_count: int = 0
    skipped_reason: str | None = None


def get_document_or_raise(db: Session, document_id) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise DocumentNotFoundError(f"document {document_id} not found")
    return document


def fetch_and_normalize_document(db: Session, document_id) -> Document:
    document = get_document_or_raise(db, document_id)
    logger.info(
        "document.processing.started document_id=%s ingest_type=%s status=%s",
        document.id,
        document.ingest_type,
        document.status,
    )

    if document.ingest_type == DocumentIngestType.URL.value:
        if not document.url:
            raise DocumentFetchError(f"document {document.id} has no url")
        fetch_result = fetch_document_content(document.url)
        normalized = normalize_text(fetch_result.cleaned_content)
        document.raw_content = fetch_result.raw_content
        document.cleaned_content = normalized
        document.title = fetch_result.title or document.title
        document.author = fetch_result.author or document.author
        document.language = fetch_result.language or document.language
        document.extraction_method = fetch_result.extraction_method
    else:
        if not document.raw_content and not document.cleaned_content:
            raise DocumentNormalizationError(f"document {document.id} has no content to normalize")
        source_text = document.cleaned_content or document.raw_content or ""
        normalized = normalize_text(source_text)
        document.raw_content = document.raw_content or source_text
        document.cleaned_content = normalized

    document.content_hash = compute_content_hash(document.cleaned_content or "")
    document.status = DocumentStatus.NORMALIZED.value
    db.commit()
    db.refresh(document)

    logger.info(
        "document.processing.completed document_id=%s status=%s extraction_method=%s content_hash=%s",
        document.id,
        document.status,
        document.extraction_method,
        document.content_hash,
    )
    return document


def process_document_pipeline(db: Session, document_id) -> DocumentProcessingResult:
    document = fetch_and_normalize_document(db, document_id)

    quality_result = evaluate_document_quality(document)
    document.quality_status = quality_result.quality_status
    db.commit()
    db.refresh(document)

    if document.quality_status != DocumentQualityStatus.ACCEPTED.value:
        logger.info(
            "document.processing.skipped document_id=%s reason=quality_rejected quality_status=%s",
            document.id,
            document.quality_status,
        )
        return DocumentProcessingResult(
            document=document,
            skipped_reason="quality_rejected",
        )

    dedup_decision = assess_document_dedup(db, document)
    db.commit()
    db.refresh(document)

    if document.dedup_status == DocumentDedupStatus.DUPLICATE.value:
        logger.info(
            "document.processing.skipped document_id=%s reason=duplicate matched_document_id=%s",
            document.id,
            dedup_decision.matched_document_id,
        )
        return DocumentProcessingResult(
            document=document,
            skipped_reason="duplicate_document",
        )

    summary = upsert_document_summary(
        db=db,
        document=document,
        quality_score=quality_result.quality_score,
    )
    chunks = rebuild_document_chunks(db, document)
    upsert_summary_embedding(db, summary)

    logger.info(
        "document.processing.pipeline_completed document_id=%s summary_id=%s chunk_count=%s dedup_status=%s",
        document.id,
        summary.id,
        len(chunks),
        document.dedup_status,
    )
    return DocumentProcessingResult(
        document=document,
        summary=summary,
        chunk_count=len(chunks),
        summary_embedding_count=1,
    )
