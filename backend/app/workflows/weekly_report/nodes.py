from __future__ import annotations

"""
Weekly report node implementations.

Each node follows a LangGraph-friendly contract:
1. read the current serialized state
2. call one domain service
3. persist a compact state patch
4. record a workflow event for traceability

The actual graph assembly will be added later, but these functions are already
structured so they can be plugged into LangGraph with minimal reshaping.
"""

from collections import defaultdict
from datetime import datetime
from typing import Callable
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.enums import (
    DocumentDedupStatus,
    DocumentQualityStatus,
    DocumentStatus,
    WorkflowStatus,
)
from app.db.models.document import Document
from app.db.models.report import Report
from app.db.models.workflow import ContextPack, RetrievalRecord
from app.services.analysis_service import upsert_document_summary
from app.services.chunk_service import rebuild_document_chunks
from app.services.cluster_service import build_weekly_clusters
from app.services.context_pack_service import build_context_pack
from app.services.dedup_service import assess_document_dedup
from app.services.ingest_processing_service import (
    DocumentNotFoundError,
    fetch_and_normalize_document,
    get_document_or_raise,
)
from app.services.fetch_service import DocumentFetchError
from app.services.normalization_service import DocumentNormalizationError
from app.services.quality_service import evaluate_document_quality
from app.services.report_export_service import export_report_markdown, mark_report_editing
from app.services.report_draft_service import draft_weekly_report
from app.services.retrieval_service import retrieve_history_for_clusters
from app.services.reviewer_service import review_report_evidence
from app.services.summary_embedding_service import upsert_summary_embedding
from app.services.workflow_service import (
    complete_workflow_event,
    fail_workflow_event,
    get_workflow_run_or_raise,
    start_workflow_event,
    update_workflow_run_state,
)
from app.workflows.weekly_report.state import (
    WeeklyReportGraphState,
    merge_weekly_report_state,
    parse_week_range,
)


logger = get_logger(__name__)

NodeHandler = Callable[[Session, WeeklyReportGraphState, object], dict]


def _state_snapshot_ref(run_id: str, node_name: str, phase: str) -> str:
    """Generate a stable pointer string that can be stored on workflow events."""
    return f"workflow_runs/{run_id}/state/{node_name}:{phase}"


def _execute_node(
    db: Session,
    state: WeeklyReportGraphState,
    *,
    node_name: str,
    handler: NodeHandler,
) -> WeeklyReportGraphState:
    """
    Execute one node with uniform event logging and state persistence.

    This wrapper keeps node implementations focused on business behavior while
    centralizing traceability, failure handling, and state-json updates.
    """
    workflow_run = get_workflow_run_or_raise(db, state["run_id"])
    input_snapshot_ref = _state_snapshot_ref(state["run_id"], node_name, "input")
    event = start_workflow_event(
        db,
        workflow_run_id=workflow_run.id,
        node_name=node_name,
        idempotency_key=f"{workflow_run.id}:{node_name}",
        input_snapshot_ref=input_snapshot_ref,
    )

    try:
        patch = handler(db, state, workflow_run)
        next_state = merge_weekly_report_state(
            state,
            {
                **patch,
                "status": node_name,
                "error_code": None,
                "error_message": None,
            },
        )
        update_workflow_run_state(
            db,
            workflow_run=workflow_run,
            state_json=next_state,
            status=WorkflowStatus.RUNNING.value,
        )
        complete_workflow_event(
            db,
            event=event,
            output_snapshot_ref=_state_snapshot_ref(state["run_id"], node_name, "output"),
        )
        logger.info(
            "workflow.node.completed workflow_run_id=%s node_name=%s",
            workflow_run.id,
            node_name,
        )
        return next_state
    except Exception as exc:
        failed_state = merge_weekly_report_state(
            state,
            {
                "status": WorkflowStatus.FAILED.value,
                "error_code": exc.__class__.__name__,
                "error_message": str(exc),
            },
        )
        update_workflow_run_state(
            db,
            workflow_run=workflow_run,
            state_json=failed_state,
            status=WorkflowStatus.FAILED.value,
        )
        fail_workflow_event(
            db,
            event=event,
            error_code=exc.__class__.__name__,
            error_message=str(exc),
        )
        raise


def collect_inputs_node(db: Session, state: WeeklyReportGraphState) -> WeeklyReportGraphState:
    """Collect candidate weekly documents from the configured time window."""

    def _handler(db: Session, state: WeeklyReportGraphState, _workflow_run: object) -> dict:
        if state["input_document_ids"]:
            candidate_ids = state["input_document_ids"]
        else:
            week_start, week_end = parse_week_range(state)
            stmt = (
                select(Document)
                .where(Document.created_at >= week_start)
                .where(Document.created_at <= week_end)
                .order_by(Document.created_at.asc())
            )
            candidate_ids = [str(document.id) for document in db.scalars(stmt).all()]

        logger.info(
            "workflow.node.collect_inputs candidate_count=%s week_start=%s week_end=%s",
            len(candidate_ids),
            state["week_range"]["start"],
            state["week_range"]["end"],
        )
        return {"input_document_ids": candidate_ids}

    return _execute_node(db, state, node_name="collect_inputs", handler=_handler)


def normalize_documents_node(db: Session, state: WeeklyReportGraphState) -> WeeklyReportGraphState:
    """Normalize collected documents so downstream nodes only touch cleaned content."""

    def _handler(db: Session, state: WeeklyReportGraphState, _workflow_run: object) -> dict:
        normalized_document_ids: list[str] = []
        skipped_document_ids: list[str] = []
        for document_id in state["input_document_ids"]:
            document = get_document_or_raise(db, UUID(document_id))

            # Already-normalized documents can be reused safely. This keeps the
            # node idempotent when a workflow is retried or resumed.
            if document.status == DocumentStatus.NORMALIZED.value and document.cleaned_content:
                normalized_document_ids.append(str(document.id))
                continue

            try:
                normalized = fetch_and_normalize_document(db, document.id)
            except (DocumentFetchError, DocumentNormalizationError, ValueError) as exc:
                # A single bad URL should not abort the entire weekly workflow.
                # We log and skip the document so the rest of the batch can
                # continue, while the document itself remains queryable for
                # follow-up debugging or manual intervention.
                document.status = DocumentStatus.FAILED.value
                db.commit()
                db.refresh(document)
                skipped_document_ids.append(str(document.id))
                logger.warning(
                    "workflow.node.normalize_documents.skipped document_id=%s error_code=%s error_message=%s",
                    document.id,
                    exc.__class__.__name__,
                    str(exc),
                )
                continue

            normalized_document_ids.append(str(normalized.id))

        logger.info(
            "workflow.node.normalize_documents normalized_count=%s skipped_count=%s",
            len(normalized_document_ids),
            len(skipped_document_ids),
        )
        return {"normalized_document_ids": normalized_document_ids}

    return _execute_node(db, state, node_name="normalize_documents", handler=_handler)


def score_and_dedup_node(db: Session, state: WeeklyReportGraphState) -> WeeklyReportGraphState:
    """Apply quality filtering and semantic deduplication before analysis begins."""

    def _handler(db: Session, state: WeeklyReportGraphState, _workflow_run: object) -> dict:
        accepted_document_ids: list[str] = []
        supporting_document_map: dict[str, list[str]] = defaultdict(list)

        for document_id in state["normalized_document_ids"]:
            document = get_document_or_raise(db, UUID(document_id))

            # Quality scoring always runs on normalized content because both the
            # heuristic and the future LLM judge should inspect the cleaned text.
            quality_result = evaluate_document_quality(document)
            document.quality_status = quality_result.quality_status
            db.commit()
            db.refresh(document)

            if document.quality_status != DocumentQualityStatus.ACCEPTED.value:
                continue

            dedup_decision = assess_document_dedup(db, document)
            db.commit()
            db.refresh(document)

            if document.dedup_status == DocumentDedupStatus.PRIMARY.value:
                accepted_document_ids.append(str(document.id))
            elif dedup_decision.matched_document_id:
                supporting_document_map[dedup_decision.matched_document_id].append(str(document.id))

        logger.info(
            "workflow.node.score_and_dedup accepted_count=%s supporting_group_count=%s",
            len(accepted_document_ids),
            len(supporting_document_map),
        )
        return {
            "accepted_document_ids": accepted_document_ids,
            "supporting_document_map": dict(supporting_document_map),
        }

    return _execute_node(db, state, node_name="score_and_dedup", handler=_handler)


def analyze_documents_node(db: Session, state: WeeklyReportGraphState) -> WeeklyReportGraphState:
    """Generate summaries, chunks, and embeddings for accepted primary documents."""

    def _handler(db: Session, state: WeeklyReportGraphState, _workflow_run: object) -> dict:
        summary_ids: list[str] = []

        for document_id in state["accepted_document_ids"]:
            document = get_document_or_raise(db, UUID(document_id))
            if not document.cleaned_content:
                raise DocumentNotFoundError(f"document {document.id} has no normalized content for analysis")

            # The workflow node intentionally performs each step explicitly
            # instead of delegating to process_document_pipeline so the graph can
            # later pause, retry, or inspect intermediate artifacts per stage.
            quality_score = 5 if document.quality_status == DocumentQualityStatus.ACCEPTED.value else None
            summary = upsert_document_summary(db=db, document=document, quality_score=quality_score)
            rebuild_document_chunks(db, document)
            upsert_summary_embedding(db, summary)
            summary_ids.append(str(summary.id))

        logger.info(
            "workflow.node.analyze_documents summary_count=%s accepted_count=%s",
            len(summary_ids),
            len(state["accepted_document_ids"]),
        )
        return {"summary_ids": summary_ids}

    return _execute_node(db, state, node_name="analyze_documents", handler=_handler)


def build_clusters_node(db: Session, state: WeeklyReportGraphState) -> WeeklyReportGraphState:
    """Aggregate accepted documents into weekly event clusters for report drafting."""

    def _handler(db: Session, state: WeeklyReportGraphState, _workflow_run: object) -> dict:
        week_start, week_end = parse_week_range(state)
        clusters = build_weekly_clusters(db, window_start=week_start, window_end=week_end)
        cluster_ids = [str(cluster.id) for cluster in clusters]
        logger.info(
            "workflow.node.build_clusters cluster_count=%s window_start=%s window_end=%s",
            len(cluster_ids),
            week_start.isoformat(),
            week_end.isoformat(),
        )
        return {"cluster_ids": cluster_ids}

    return _execute_node(db, state, node_name="build_clusters", handler=_handler)


def retrieve_history_node(db: Session, state: WeeklyReportGraphState) -> WeeklyReportGraphState:
    """Retrieve historical summaries and evidence chunks for the current clusters."""

    def _handler(db: Session, state: WeeklyReportGraphState, workflow_run: object) -> dict:
        retrieval_record = retrieve_history_for_clusters(
            db,
            workflow_run=workflow_run,
            cluster_ids=[UUID(cluster_id) for cluster_id in state["cluster_ids"]],
        )
        logger.info(
            "workflow.node.retrieve_history summary_hit_count=%s chunk_hit_count=%s",
            len(retrieval_record.retrieved_summary_ids or []),
            len(retrieval_record.retrieved_chunk_ids or []),
        )
        return {
            "retrieval_query": retrieval_record.query_text,
            "retrieved_summary_ids": [str(item_id) for item_id in (retrieval_record.retrieved_summary_ids or [])],
            "retrieved_chunk_ids": [str(item_id) for item_id in (retrieval_record.retrieved_chunk_ids or [])],
        }

    return _execute_node(db, state, node_name="retrieve_history", handler=_handler)


def backfill_evidence_node(db: Session, state: WeeklyReportGraphState) -> WeeklyReportGraphState:
    """Build and persist the context pack referenced by downstream draft/review nodes."""

    def _handler(db: Session, state: WeeklyReportGraphState, workflow_run: object) -> dict:
        retrieval_record = db.scalar(
            select(RetrievalRecord)
            .where(RetrievalRecord.workflow_run_id == workflow_run.id)
            .order_by(RetrievalRecord.created_at.desc())
        )
        if retrieval_record is None:
            raise ValueError(f"workflow_run {workflow_run.id} has no retrieval_record to backfill")

        context_pack = build_context_pack(
            db,
            workflow_run=workflow_run,
            cluster_ids=[UUID(cluster_id) for cluster_id in state["cluster_ids"]],
            retrieval_record=retrieval_record,
        )
        logger.info(
            "workflow.node.backfill_evidence context_pack_id=%s summary_count=%s chunk_count=%s",
            context_pack.id,
            len(context_pack.context_json.get("historical_summaries", [])),
            len(context_pack.context_json.get("evidence_chunks", [])),
        )
        return {"context_pack_ref": str(context_pack.id)}

    return _execute_node(db, state, node_name="backfill_evidence", handler=_handler)


def draft_weekly_report_node(db: Session, state: WeeklyReportGraphState) -> WeeklyReportGraphState:
    """Render the current cluster set and context pack into a persisted draft report."""

    def _handler(db: Session, state: WeeklyReportGraphState, workflow_run: object) -> dict:
        if not state.get("context_pack_ref"):
            raise ValueError("context_pack_ref is required before drafting report")

        context_pack = db.get(ContextPack, UUID(state["context_pack_ref"]))
        if context_pack is None:
            raise ValueError(f"context_pack {state['context_pack_ref']} not found")

        report = draft_weekly_report(
            db,
            workflow_run=workflow_run,
            cluster_ids=[UUID(cluster_id) for cluster_id in state["cluster_ids"]],
            context_pack=context_pack,
        )
        logger.info(
            "workflow.node.draft_weekly_report report_id=%s content_length=%s",
            report.id,
            len(report.content_md),
        )
        return {
            "report_id": str(report.id),
            "draft_report_ref": str(report.id),
        }

    return _execute_node(db, state, node_name="draft_weekly_report", handler=_handler)


def review_evidence_node(db: Session, state: WeeklyReportGraphState) -> WeeklyReportGraphState:
    """Review the draft report against the persisted context pack and evidence checks."""

    def _handler(db: Session, state: WeeklyReportGraphState, _workflow_run: object) -> dict:
        if not state.get("report_id"):
            raise ValueError("report_id is required before evidence review")
        if not state.get("context_pack_ref"):
            raise ValueError("context_pack_ref is required before evidence review")

        report = db.get(Report, UUID(state["report_id"]))
        if report is None:
            raise ValueError(f"report {state['report_id']} not found")

        context_pack = db.get(ContextPack, UUID(state["context_pack_ref"]))
        if context_pack is None:
            raise ValueError(f"context_pack {state['context_pack_ref']} not found")

        review_result = review_report_evidence(
            db,
            report=report,
            context_pack=context_pack,
        )
        next_retry_count = state["retry_count"]
        if review_result.decision != "pass":
            next_retry_count += 1

        logger.info(
            "workflow.node.review_evidence report_id=%s decision=%s retry_count=%s",
            report.id,
            review_result.decision,
            next_retry_count,
        )
        return {
            "review_decision": review_result.decision,
            "review_checks": review_result.checks,
            "retry_count": next_retry_count,
        }

    return _execute_node(db, state, node_name="review_evidence", handler=_handler)


def human_edit_node(db: Session, state: WeeklyReportGraphState) -> WeeklyReportGraphState:
    """Pause the workflow at the human-edit boundary and mark the report editable."""

    def _handler(db: Session, state: WeeklyReportGraphState, workflow_run: object) -> dict:
        if not state.get("report_id"):
            raise ValueError("report_id is required before human_edit")

        report = db.get(Report, UUID(state["report_id"]))
        if report is None:
            raise ValueError(f"report {state['report_id']} not found")

        mark_report_editing(db, report)
        logger.info(
            "workflow.node.human_edit report_id=%s workflow_run_id=%s",
            report.id,
            workflow_run.id,
        )
        return {"human_edit_status": "waiting"}

    next_state = _execute_node(db, state, node_name="human_edit", handler=_handler)
    workflow_run = get_workflow_run_or_raise(db, next_state["run_id"])
    next_state = merge_weekly_report_state(next_state, {"status": WorkflowStatus.WAITING_HUMAN_EDIT.value})
    update_workflow_run_state(
        db,
        workflow_run=workflow_run,
        state_json=next_state,
        status=WorkflowStatus.WAITING_HUMAN_EDIT.value,
    )
    return next_state


def export_markdown_node(db: Session, state: WeeklyReportGraphState) -> WeeklyReportGraphState:
    """Export the report markdown to disk and mark the workflow/report as completed."""

    def _handler(db: Session, state: WeeklyReportGraphState, workflow_run: object) -> dict:
        if not state.get("report_id"):
            raise ValueError("report_id is required before export_markdown")

        report = db.get(Report, UUID(state["report_id"]))
        if report is None:
            raise ValueError(f"report {state['report_id']} not found")

        export_path = export_report_markdown(db, report)
        logger.info(
            "workflow.node.export_markdown report_id=%s export_path=%s",
            report.id,
            export_path,
        )
        return {
            "human_edit_status": "approved",
            "exported_markdown_path": export_path,
        }

    next_state = _execute_node(db, state, node_name="export_markdown", handler=_handler)
    workflow_run = get_workflow_run_or_raise(db, next_state["run_id"])
    next_state = merge_weekly_report_state(next_state, {"status": WorkflowStatus.COMPLETED.value})
    update_workflow_run_state(
        db,
        workflow_run=workflow_run,
        state_json=next_state,
        status=WorkflowStatus.COMPLETED.value,
        finished_at=datetime.now().astimezone(),
    )
    return next_state
