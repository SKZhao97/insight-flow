from __future__ import annotations

"""Context-pack assembly for weekly report generation."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.models.cluster import Cluster
from app.db.models.document import DocumentChunk
from app.db.models.summary import Summary
from app.db.models.workflow import ContextPack, RetrievalRecord, WorkflowRun


logger = get_logger(__name__)

CONTEXT_PACK_BUILD_VERSION = "m04_context_pack_v1"


def build_context_pack(
    db: Session,
    *,
    workflow_run: WorkflowRun,
    cluster_ids: list,
    retrieval_record: RetrievalRecord,
) -> ContextPack:
    """
    Materialize the exact context payload used by the report-drafting stage.

    Persisting the pack as its own record makes later debugging much easier:
    we can inspect exactly which clusters, summaries, and evidence chunks were
    given to the draft step for one workflow run.
    """
    clusters = list(db.scalars(select(Cluster).where(Cluster.id.in_(cluster_ids))).all())
    summaries = []
    if retrieval_record.retrieved_summary_ids:
        summaries = list(
            db.scalars(select(Summary).where(Summary.id.in_(retrieval_record.retrieved_summary_ids))).all()
        )
    chunks = []
    if retrieval_record.retrieved_chunk_ids:
        chunks = list(
            db.scalars(select(DocumentChunk).where(DocumentChunk.id.in_(retrieval_record.retrieved_chunk_ids))).all()
        )

    context_json = {
        # Clusters capture the current-week storyline that the report should
        # emphasize, while the historical sections supply longitudinal context.
        "clusters": [
            {
                "id": str(cluster.id),
                "title": cluster.title,
                "summary": cluster.summary,
            }
            for cluster in clusters
        ],
        "historical_summaries": [
            {
                "id": str(summary.id),
                "short_summary": summary.short_summary,
                "key_points": summary.key_points,
                "tags": summary.tags,
                "category": summary.category,
            }
            for summary in summaries
        ],
        "evidence_chunks": [
            {
                "id": str(chunk.id),
                "document_id": str(chunk.document_id),
                "chunk_text": chunk.chunk_text,
                "chunk_index": chunk.chunk_index,
            }
            for chunk in chunks
        ],
    }

    pack = ContextPack(
        workflow_run_id=workflow_run.id,
        context_json=context_json,
        build_version=CONTEXT_PACK_BUILD_VERSION,
    )
    db.add(pack)
    db.commit()
    db.refresh(pack)

    logger.info(
        "context_pack.built workflow_run_id=%s context_pack_id=%s cluster_count=%s summary_count=%s chunk_count=%s",
        workflow_run.id,
        pack.id,
        len(context_json["clusters"]),
        len(context_json["historical_summaries"]),
        len(context_json["evidence_chunks"]),
    )
    return pack
