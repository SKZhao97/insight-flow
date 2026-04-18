from __future__ import annotations

"""Report-drafting services for the MVP weekly report workflow."""

from collections import defaultdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.enums import ReportItemType, ReportStatus, ReportType
from app.db.models.cluster import Cluster, ClusterItem
from app.db.models.document import Document
from app.db.models.report import Report, ReportItem
from app.db.models.summary import Summary
from app.db.models.workflow import ContextPack, WorkflowRun


logger = get_logger(__name__)


def draft_weekly_report(
    db: Session,
    *,
    workflow_run: WorkflowRun,
    cluster_ids: list,
    context_pack: ContextPack,
) -> Report:
    """
    Draft a weekly markdown report from cluster-level inputs and historical context.

    The MVP renderer is deterministic and template-like on purpose. This keeps
    the report step debuggable before we introduce a more flexible LLM writer.
    """
    clusters = list(db.scalars(select(Cluster).where(Cluster.id.in_(cluster_ids)).order_by(Cluster.created_at.asc())).all())
    report_lines = [f"# Weekly AI Report ({workflow_run.week_start:%Y-%m-%d} to {workflow_run.week_end:%Y-%m-%d})", ""]

    report = Report(
        type=ReportType.WEEKLY.value,
        title=f"Weekly AI Report - {workflow_run.week_start:%Y-%m-%d}",
        window_start=workflow_run.week_start,
        window_end=workflow_run.week_end,
        content_md="",
        status=ReportStatus.DRAFT.value,
        generated_by_run_id=workflow_run.id,
    )
    db.add(report)
    db.flush()

    for idx, cluster in enumerate(clusters, start=1):
        report_lines.append(f"## {idx}. {cluster.title}")
        report_lines.append(cluster.summary)
        report_lines.append("")

        item_stmt = (
            select(ClusterItem, Summary, Document)
            .join(Summary, Summary.document_id == ClusterItem.document_id)
            .join(Document, Document.id == ClusterItem.document_id)
            .where(ClusterItem.cluster_id == cluster.id)
            .order_by(ClusterItem.position.asc())
        )
        rows = db.execute(item_stmt).all()
        for position, (cluster_item, summary, document) in enumerate(rows, start=1):
            # ReportItem is the durable citation layer between generated output
            # and the underlying documents, summaries, and clusters.
            report_lines.append(f"- {summary.short_summary}")
            report_item = ReportItem(
                report_id=report.id,
                summary_id=summary.id,
                document_id=document.id,
                cluster_id=cluster.id,
                source_url=document.canonical_url or document.url or f"document:{document.id}",
                item_type=ReportItemType.EVENT.value,
                position=position + ((idx - 1) * 100),
            )
            db.add(report_item)
        report_lines.append("")

    if context_pack.context_json.get("historical_summaries"):
        # Historical context is intentionally kept separate so readers can tell
        # what is "this week" versus what is relevant background memory.
        report_lines.append("## Historical Context")
        for item in context_pack.context_json["historical_summaries"][:3]:
            report_lines.append(f"- {item['short_summary']}")
        report_lines.append("")

    report.content_md = "\n".join(report_lines).strip()
    db.commit()
    db.refresh(report)

    logger.info(
        "report.drafted workflow_run_id=%s report_id=%s cluster_count=%s content_length=%s",
        workflow_run.id,
        report.id,
        len(clusters),
        len(report.content_md),
    )
    return report
