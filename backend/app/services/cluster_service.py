from __future__ import annotations

"""Services for grouping analyzed weekly documents into event-level clusters."""

from collections import defaultdict
from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, selectinload

from app.core.logging import get_logger
from app.db.enums import ClusterStatus, ClusterType, DocumentDedupStatus, DocumentQualityStatus
from app.db.models.cluster import Cluster, ClusterItem
from app.db.models.document import Document
from app.db.models.summary import Summary
from app.db.models.workflow import WorkflowRun


logger = get_logger(__name__)

CLUSTER_BUILD_VERSION = "m04_cluster_v1"


def _cluster_key(summary: Summary) -> str:
    # The MVP clustering heuristic is intentionally simple: category + first tag
    # gives us a deterministic event bucket without introducing another model.
    tags = summary.tags or []
    primary_tag = tags[0] if tags else "general"
    return f"{summary.category}:{primary_tag}"


def build_weekly_clusters(
    db: Session,
    *,
    workflow_run: WorkflowRun,
    document_ids: list,
    window_start: datetime,
    window_end: datetime,
) -> list[Cluster]:
    """
    Build weekly clusters from accepted primary documents inside one time window.

    The workflow later drafts reports from clusters rather than from individual
    documents so the report reads like event synthesis instead of a raw list of
    articles.
    """
    effective_timestamp = func.coalesce(Document.published_at, Document.created_at)
    summary_stmt = (
        select(Summary)
        .join(Document, Summary.document_id == Document.id)
        .where(Document.id.in_(document_ids))
        .where(effective_timestamp >= window_start)
        .where(effective_timestamp <= window_end)
        .where(Document.quality_status == DocumentQualityStatus.ACCEPTED.value)
        .where(Document.dedup_status == DocumentDedupStatus.PRIMARY.value)
        .options(selectinload(Summary.document))
        .order_by(effective_timestamp.asc())
    )
    summaries = list(db.scalars(summary_stmt).all())

    # Clusters are scoped to one workflow run. Rebuilding a run must be
    # deterministic, but one run must never delete another run's cluster set.
    db.execute(
        delete(ClusterItem).where(
            ClusterItem.cluster_id.in_(
                select(Cluster.id).where(Cluster.workflow_run_id == workflow_run.id)
            )
        )
    )
    db.execute(delete(Cluster).where(Cluster.workflow_run_id == workflow_run.id))
    db.flush()

    grouped: dict[str, list[Summary]] = defaultdict(list)
    for summary in summaries:
        grouped[_cluster_key(summary)].append(summary)

    created_clusters: list[Cluster] = []
    for _, group in grouped.items():
        first = group[0]
        title = f"{first.category.replace('_', ' ').title()}: {(first.tags or ['general'])[0]}"
        cluster_summary = " ".join(summary.short_summary for summary in group[:3])[:1000]
        cluster = Cluster(
            workflow_run_id=workflow_run.id,
            title=title,
            summary=cluster_summary,
            cluster_type=ClusterType.WEEKLY_EVENT.value,
            window_start=window_start,
            window_end=window_end,
            build_version=CLUSTER_BUILD_VERSION,
            status=ClusterStatus.ACTIVE.value,
        )
        db.add(cluster)
        db.flush()

        for idx, summary in enumerate(group):
            item = ClusterItem(
                cluster_id=cluster.id,
                document_id=summary.document_id,
                position=idx,
            )
            db.add(item)

        created_clusters.append(cluster)

    db.commit()
    for cluster in created_clusters:
        db.refresh(cluster)

    logger.info(
        "clusters.built window_start=%s window_end=%s cluster_count=%s build_version=%s",
        window_start.isoformat(),
        window_end.isoformat(),
        len(created_clusters),
        CLUSTER_BUILD_VERSION,
    )
    return created_clusters
