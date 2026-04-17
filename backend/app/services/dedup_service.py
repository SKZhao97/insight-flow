from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.enums import DocumentDedupStatus, DocumentQualityStatus, DocumentRelationType
from app.db.models.document import Document, DocumentRelation
from app.services.embedding_service import cosine_similarity, embed_text


logger = get_logger(__name__)

NEAR_DUPLICATE_THRESHOLD = 0.97
SUPPORTING_SOURCE_THRESHOLD = 0.82


@dataclass(slots=True)
class DedupDecision:
    dedup_status: str
    matched_document_id: str | None = None
    relation_type: str | None = None
    similarity_score: float | None = None


def _choose_primary(current: Document, candidate: Document) -> tuple[Document, Document]:
    current_time = current.published_at or current.created_at
    candidate_time = candidate.published_at or candidate.created_at
    if candidate_time <= current_time:
        return candidate, current
    return current, candidate


def assess_document_dedup(db: Session, document: Document) -> DedupDecision:
    if not document.cleaned_content:
        document.dedup_status = DocumentDedupStatus.PENDING.value
        return DedupDecision(dedup_status=document.dedup_status)

    stmt = (
        select(Document)
        .where(Document.id != document.id)
        .where(Document.quality_status == DocumentQualityStatus.ACCEPTED.value)
        .where(Document.cleaned_content.is_not(None))
        .order_by(Document.created_at.asc())
    )
    candidates = list(db.scalars(stmt).all())

    current_embedding = embed_text(document.cleaned_content)
    best_candidate: Document | None = None
    best_similarity = 0.0

    for candidate in candidates:
        if candidate.content_hash == document.content_hash:
            best_candidate = candidate
            best_similarity = 1.0
            break

        candidate_text = candidate.cleaned_content or ""
        similarity = cosine_similarity(current_embedding, embed_text(candidate_text))
        if similarity > best_similarity:
            best_candidate = candidate
            best_similarity = similarity

    if not best_candidate:
        document.dedup_status = DocumentDedupStatus.PRIMARY.value
        logger.info("document.dedup.primary document_id=%s matched_document_id=- similarity=0.0", document.id)
        return DedupDecision(dedup_status=document.dedup_status)

    primary_doc, secondary_doc = _choose_primary(document, best_candidate)

    if best_similarity >= NEAR_DUPLICATE_THRESHOLD:
        relation_type = DocumentRelationType.NEAR_DUPLICATE.value
        secondary_doc.dedup_status = DocumentDedupStatus.DUPLICATE.value
    elif best_similarity >= SUPPORTING_SOURCE_THRESHOLD:
        relation_type = DocumentRelationType.SUPPORTING_SOURCE.value
        secondary_doc.dedup_status = DocumentDedupStatus.SUPPORTING.value
    else:
        document.dedup_status = DocumentDedupStatus.PRIMARY.value
        logger.info(
            "document.dedup.primary document_id=%s matched_document_id=%s similarity=%.4f",
            document.id,
            best_candidate.id,
            best_similarity,
        )
        return DedupDecision(dedup_status=document.dedup_status)

    primary_doc.dedup_status = DocumentDedupStatus.PRIMARY.value

    existing_relation_stmt = (
        select(DocumentRelation)
        .where(DocumentRelation.document_id == secondary_doc.id)
        .where(DocumentRelation.related_document_id == primary_doc.id)
        .where(DocumentRelation.relation_type == relation_type)
    )
    relation = db.scalar(existing_relation_stmt)
    if relation is None:
        relation = DocumentRelation(
            document_id=secondary_doc.id,
            related_document_id=primary_doc.id,
            relation_type=relation_type,
            similarity_score=best_similarity,
        )
        db.add(relation)
    else:
        relation.similarity_score = best_similarity

    logger.info(
        "document.dedup.related document_id=%s matched_document_id=%s relation_type=%s similarity=%.4f dedup_status=%s",
        secondary_doc.id,
        primary_doc.id,
        relation_type,
        best_similarity,
        secondary_doc.dedup_status,
    )
    return DedupDecision(
        dedup_status=secondary_doc.dedup_status,
        matched_document_id=str(primary_doc.id),
        relation_type=relation_type,
        similarity_score=best_similarity,
    )
