from __future__ import annotations

from dataclasses import dataclass

from app.core.logging import get_logger
from app.db.enums import DocumentQualityStatus
from app.db.models.document import Document


logger = get_logger(__name__)


@dataclass(slots=True)
class QualityEvaluation:
    quality_score: int
    quality_status: str
    rationale: str


def evaluate_document_quality(document: Document) -> QualityEvaluation:
    content = (document.cleaned_content or "").strip()
    word_count = len(content.split())
    line_count = len([line for line in content.splitlines() if line.strip()])

    if word_count < 20 or len(content) < 120:
        result = QualityEvaluation(
            quality_score=1,
            quality_status=DocumentQualityStatus.REJECTED_LOW_VALUE.value,
            rationale="content_too_short",
        )
    elif word_count < 60:
        result = QualityEvaluation(
            quality_score=3,
            quality_status=DocumentQualityStatus.ACCEPTED.value,
            rationale="short_but_usable",
        )
    elif line_count >= 4:
        result = QualityEvaluation(
            quality_score=5,
            quality_status=DocumentQualityStatus.ACCEPTED.value,
            rationale="sufficient_substance",
        )
    else:
        result = QualityEvaluation(
            quality_score=4,
            quality_status=DocumentQualityStatus.ACCEPTED.value,
            rationale="usable_substance",
        )

    logger.info(
        "document.quality.evaluated document_id=%s quality_status=%s quality_score=%s rationale=%s",
        document.id,
        result.quality_status,
        result.quality_score,
        result.rationale,
    )
    return result
