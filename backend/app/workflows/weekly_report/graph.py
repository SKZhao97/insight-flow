from __future__ import annotations

"""LangGraph assembly for the weekly report workflow."""

from contextlib import contextmanager
from collections.abc import Callable
from typing import Any

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.workflows.weekly_report.nodes import (
    analyze_documents_node,
    backfill_evidence_node,
    build_clusters_node,
    collect_inputs_node,
    draft_weekly_report_node,
    export_markdown_node,
    human_edit_node,
    normalize_documents_node,
    retrieve_history_node,
    review_evidence_node,
    score_and_dedup_node,
)
from app.workflows.weekly_report.state import WeeklyReportGraphState


logger = get_logger(__name__)

DBSessionFactory = Callable[[], Session]

MAX_REVIEW_RETRIES = 2


def _normalize_postgres_conn_string(conn_string: str) -> str:
    """
    Convert the SQLAlchemy-style database URL into the psycopg flavor expected
    by LangGraph's PostgresSaver.
    """

    if conn_string.startswith("postgresql+psycopg://"):
        return conn_string.replace("postgresql+psycopg://", "postgresql://", 1)
    return conn_string


def _with_session(
    db_session_factory: DBSessionFactory,
    node_fn: Callable[[Session, WeeklyReportGraphState], WeeklyReportGraphState],
) -> Callable[[WeeklyReportGraphState], WeeklyReportGraphState]:
    """
    Adapt session-bound node functions to the single-argument LangGraph contract.

    Every node gets a fresh SQLAlchemy session so retries, resumes, and later
    parallel execution are isolated from one another.
    """

    def _runner(state: WeeklyReportGraphState) -> WeeklyReportGraphState:
        db = db_session_factory()
        try:
            return node_fn(db, state)
        finally:
            db.close()

    return _runner


def _review_router(state: WeeklyReportGraphState) -> str:
    """
    Decide the next edge after review.

    The routing stays intentionally conservative:
    - `need_more_evidence` returns to retrieval
    - `too_redundant` / `conclusion_too_strong` re-draft from the existing context
    - after too many retries, the workflow yields to human edit instead of looping
    """

    decision = state.get("review_decision")
    retry_count = state.get("retry_count", 0)

    if retry_count >= MAX_REVIEW_RETRIES:
        logger.warning(
            "weekly_report_graph.review_router max_retry_reached decision=%s retry_count=%s",
            decision,
            retry_count,
        )
        return "human_edit"

    if decision == "need_more_evidence":
        return "retrieve_history"
    if decision in {"too_redundant", "conclusion_too_strong"}:
        return "draft_weekly_report"
    return "human_edit"


def build_weekly_report_graph(
    *,
    db_session_factory: DBSessionFactory,
    checkpointer: Any | None = None,
    interrupt_after_human_edit: bool = True,
):
    """
    Compile the MVP weekly-report graph.

    We default to an in-memory checkpointer in lightweight development flows.
    Production-like flows should use the Postgres-backed saver so interrupts and
    resumes survive process restarts.
    """

    builder = StateGraph(WeeklyReportGraphState)

    builder.add_node("collect_inputs", _with_session(db_session_factory, collect_inputs_node))
    builder.add_node("normalize_documents", _with_session(db_session_factory, normalize_documents_node))
    builder.add_node("score_and_dedup", _with_session(db_session_factory, score_and_dedup_node))
    builder.add_node("analyze_documents", _with_session(db_session_factory, analyze_documents_node))
    builder.add_node("build_clusters", _with_session(db_session_factory, build_clusters_node))
    builder.add_node("retrieve_history", _with_session(db_session_factory, retrieve_history_node))
    builder.add_node("backfill_evidence", _with_session(db_session_factory, backfill_evidence_node))
    builder.add_node("draft_weekly_report", _with_session(db_session_factory, draft_weekly_report_node))
    builder.add_node("review_evidence", _with_session(db_session_factory, review_evidence_node))
    builder.add_node("human_edit", _with_session(db_session_factory, human_edit_node))
    builder.add_node("export_markdown", _with_session(db_session_factory, export_markdown_node))

    builder.add_edge(START, "collect_inputs")
    builder.add_edge("collect_inputs", "normalize_documents")
    builder.add_edge("normalize_documents", "score_and_dedup")
    builder.add_edge("score_and_dedup", "analyze_documents")
    builder.add_edge("analyze_documents", "build_clusters")
    builder.add_edge("build_clusters", "retrieve_history")
    builder.add_edge("retrieve_history", "backfill_evidence")
    builder.add_edge("backfill_evidence", "draft_weekly_report")
    builder.add_edge("draft_weekly_report", "review_evidence")
    builder.add_conditional_edges(
        "review_evidence",
        _review_router,
        {
            "retrieve_history": "retrieve_history",
            "draft_weekly_report": "draft_weekly_report",
            "human_edit": "human_edit",
        },
    )
    builder.add_edge("human_edit", "export_markdown")
    builder.add_edge("export_markdown", END)

    compiled = builder.compile(
        checkpointer=checkpointer or InMemorySaver(),
        interrupt_after=["human_edit"] if interrupt_after_human_edit else None,
        name="weekly_report_graph",
    )
    logger.info(
        "weekly_report_graph.compiled interrupt_after_human_edit=%s checkpointer=%s",
        interrupt_after_human_edit,
        type(checkpointer or InMemorySaver()).__name__,
    )
    return compiled


@contextmanager
def build_weekly_report_graph_with_postgres_checkpointer(
    *,
    db_session_factory: DBSessionFactory,
    conn_string: str,
    interrupt_after_human_edit: bool = True,
):
    """
    Compile the graph with a Postgres-backed checkpointer.

    LangGraph exposes the saver as a context-managed resource, so this helper
    keeps the saver open for the lifetime of the compiled graph usage.
    """

    normalized_conn_string = _normalize_postgres_conn_string(conn_string)
    with PostgresSaver.from_conn_string(normalized_conn_string) as saver:
        saver.setup()
        compiled = build_weekly_report_graph(
            db_session_factory=db_session_factory,
            checkpointer=saver,
            interrupt_after_human_edit=interrupt_after_human_edit,
        )
        logger.info(
            "weekly_report_graph.postgres_checkpointer_ready conn_string=%s",
            normalized_conn_string,
        )
        yield compiled
