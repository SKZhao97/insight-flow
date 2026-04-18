from __future__ import annotations

"""Retrieval services for the weekly-report RAG stage."""

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.core.logging import get_logger
from app.db.models.cluster import Cluster, ClusterItem
from app.db.models.document import Document, DocumentChunk
from app.db.models.summary import Summary, SummaryEmbedding
from app.db.models.workflow import RetrievalRecord, WorkflowRun
from app.services.embedding_service import EMBEDDING_MODEL_NAME, cosine_similarity, embed_text


logger = get_logger(__name__)


def retrieve_history_for_clusters(
    db: Session,
    *,
    workflow_run: WorkflowRun,
    cluster_ids: list,
    history_days: int = 30,
    top_k: int = 5,
    chunk_top_k: int = 8,
) -> RetrievalRecord:
    """
    Retrieve historical summaries first, then backfill original evidence chunks.

    This dual-context strategy avoids the common "summary of summaries" failure
    mode: summary embeddings are cheap and semantically useful for recall, while
    raw chunks recover the factual details needed for evidence review later.
    """
    clusters = list(
        db.scalars(select(Cluster).where(Cluster.id.in_(cluster_ids)).order_by(Cluster.created_at.asc())).all()
    )
    query_text = "\n".join(cluster.summary for cluster in clusters)
    query_embedding = embed_text(query_text)

    history_cutoff = (workflow_run.week_start or datetime.now().astimezone()) - timedelta(days=history_days)
    effective_timestamp = func.coalesce(Document.published_at, Document.created_at)
    summary_stmt = (
        select(SummaryEmbedding)
        .join(Summary, SummaryEmbedding.summary_id == Summary.id)
        .join(Document, Summary.document_id == Document.id)
        .options(selectinload(SummaryEmbedding.summary))
        .where(SummaryEmbedding.embedding_model == EMBEDDING_MODEL_NAME)
        .where(effective_timestamp >= history_cutoff)
        .where(effective_timestamp < workflow_run.week_start)
    )
    summary_embeddings = list(db.scalars(summary_stmt).all())

    scored_summaries: list[tuple[float, SummaryEmbedding]] = []
    for item in summary_embeddings:
        # pgvector-backed arrays do not support truthiness checks reliably, so
        # we guard with an explicit `is not None` instead of using `or []`.
        vector = item.embedding if item.embedding is not None else []
        score = cosine_similarity(query_embedding, vector)
        scored_summaries.append((score, item))
    scored_summaries.sort(key=lambda pair: pair[0], reverse=True)
    top_summaries = scored_summaries[:top_k]
    retrieved_summary_ids = [item.summary_id for _, item in top_summaries]

    retrieved_chunk_ids: list = []
    chunk_scores: dict[str, float] = {}
    if retrieved_summary_ids:
        chunk_stmt = (
            select(DocumentChunk)
            .join(Summary, Summary.document_id == DocumentChunk.document_id)
            .where(Summary.id.in_(retrieved_summary_ids))
        )
        chunks = list(db.scalars(chunk_stmt).all())
        scored_chunks: list[tuple[float, DocumentChunk]] = []
        for chunk in chunks:
            # Chunk backfill restores source-level evidence after summary-level
            # retrieval has identified which historical documents are relevant.
            vector = chunk.embedding if chunk.embedding is not None else []
            score = cosine_similarity(query_embedding, vector)
            scored_chunks.append((score, chunk))
        scored_chunks.sort(key=lambda pair: pair[0], reverse=True)
        top_chunks = scored_chunks[:chunk_top_k]
        retrieved_chunk_ids = [chunk.id for _, chunk in top_chunks]
        chunk_scores = {str(chunk.id): score for score, chunk in top_chunks}

    record = RetrievalRecord(
        workflow_run_id=workflow_run.id,
        query_text=query_text[:4000],
        filter_json={
            "cluster_ids": [str(cluster_id) for cluster_id in cluster_ids],
            "history_days": history_days,
            "top_k": top_k,
            "chunk_top_k": chunk_top_k,
        },
        retrieved_summary_ids=retrieved_summary_ids or None,
        retrieved_chunk_ids=retrieved_chunk_ids or None,
        score_snapshot={
            # JSONB serialization must receive plain Python floats instead of
            # numpy scalar values returned by vector math helpers.
            "summary_scores": {str(item.summary_id): float(score) for score, item in top_summaries},
            "chunk_scores": {key: float(value) for key, value in chunk_scores.items()},
        },
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    logger.info(
        "retrieval.completed workflow_run_id=%s cluster_count=%s summary_hits=%s chunk_hits=%s",
        workflow_run.id,
        len(cluster_ids),
        len(retrieved_summary_ids),
        len(retrieved_chunk_ids),
    )
    return record
