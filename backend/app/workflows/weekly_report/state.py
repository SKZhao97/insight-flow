from __future__ import annotations

"""
State helpers for the Weekly Report workflow.

The state intentionally keeps large text blobs out of memory and out of the
serialized checkpoint payload. We only persist identifiers and lightweight
metadata here, then load full records from the database inside node functions.
"""

from datetime import datetime
from typing import Any, NotRequired, TypedDict

from app.db.enums import WorkflowStatus


class WeekRange(TypedDict):
    """Serialized execution window used by the weekly report workflow."""

    start: str
    end: str


class WeeklyReportGraphState(TypedDict):
    """
    Serialized state shared across weekly-report nodes.

    The schema mirrors the architecture document and remains JSON-friendly so it
    can be stored in `workflow_runs.state_json` and, later, in LangGraph
    checkpoint storage without custom encoders.
    """

    run_id: str
    status: str
    week_range: WeekRange
    input_document_ids: list[str]
    normalized_document_ids: list[str]
    accepted_document_ids: list[str]
    supporting_document_map: dict[str, list[str]]
    summary_ids: list[str]
    cluster_ids: list[str]
    retrieved_summary_ids: list[str]
    retrieved_chunk_ids: list[str]
    review_checks: dict[str, Any]
    retry_count: int
    draft_constraints: dict[str, Any]
    retrieval_overrides: dict[str, Any]
    report_id: NotRequired[str | None]
    retrieval_query: NotRequired[str | None]
    context_pack_ref: NotRequired[str | None]
    draft_report_ref: NotRequired[str | None]
    exported_markdown_path: NotRequired[str | None]
    review_decision: NotRequired[str | None]
    human_edit_status: NotRequired[str | None]
    error_code: NotRequired[str | None]
    error_message: NotRequired[str | None]


def build_initial_weekly_report_state(
    *,
    run_id: str,
    week_start: datetime,
    week_end: datetime,
    input_document_ids: list[str] | None = None,
) -> WeeklyReportGraphState:
    """Build the canonical initial state for a new weekly report execution."""
    return WeeklyReportGraphState(
        run_id=run_id,
        report_id=None,
        status=WorkflowStatus.RUNNING.value,
        week_range={
            "start": week_start.isoformat(),
            "end": week_end.isoformat(),
        },
        input_document_ids=input_document_ids or [],
        normalized_document_ids=[],
        accepted_document_ids=[],
        supporting_document_map={},
        summary_ids=[],
        cluster_ids=[],
        retrieval_query=None,
        retrieved_summary_ids=[],
        retrieved_chunk_ids=[],
        draft_constraints={},
        retrieval_overrides={},
        context_pack_ref=None,
        draft_report_ref=None,
        exported_markdown_path=None,
        review_decision=None,
        review_checks={},
        human_edit_status=None,
        retry_count=0,
        error_code=None,
        error_message=None,
    )


def merge_weekly_report_state(
    state: WeeklyReportGraphState,
    patch: dict[str, Any],
) -> WeeklyReportGraphState:
    """
    Apply a shallow patch while preserving the JSON-serializable state shape.

    LangGraph nodes normally return partial updates. This helper gives us the
    same contract today even before the final graph assembly lands.
    """
    merged = dict(state)
    merged.update(patch)
    return WeeklyReportGraphState(**merged)


def parse_week_range(state: WeeklyReportGraphState) -> tuple[datetime, datetime]:
    """Decode the serialized window into timezone-aware datetime objects."""
    return (
        datetime.fromisoformat(state["week_range"]["start"]),
        datetime.fromisoformat(state["week_range"]["end"]),
    )
