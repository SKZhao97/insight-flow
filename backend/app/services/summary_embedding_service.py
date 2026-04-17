from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.models.summary import Summary, SummaryEmbedding
from app.services.embedding_service import EMBEDDING_MODEL_NAME, embed_text, log_embedding_created


logger = get_logger(__name__)

EMBEDDING_SOURCE = "short_summary"


def upsert_summary_embedding(db: Session, summary: Summary) -> SummaryEmbedding:
    embedding_input = " ".join([summary.short_summary, *summary.key_points])
    vector = embed_text(embedding_input)

    stmt = (
        select(SummaryEmbedding)
        .where(SummaryEmbedding.summary_id == summary.id)
        .where(SummaryEmbedding.embedding_model == EMBEDDING_MODEL_NAME)
        .where(SummaryEmbedding.embedding_source == EMBEDDING_SOURCE)
    )
    record = db.scalar(stmt)
    if record is None:
        record = SummaryEmbedding(
            summary_id=summary.id,
            embedding_model=EMBEDDING_MODEL_NAME,
            embedding_source=EMBEDDING_SOURCE,
            embedding=vector,
        )
        db.add(record)
    else:
        record.embedding = vector

    db.commit()
    db.refresh(record)
    log_embedding_created("summary", summary.id, EMBEDDING_SOURCE)

    logger.info(
        "summary.embedding.upserted summary_id=%s embedding_id=%s embedding_model=%s",
        summary.id,
        record.id,
        record.embedding_model,
    )
    return record
