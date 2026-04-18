from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas.workflow import WeeklyWorkflowRunRequest, WeeklyWorkflowRunResponse
from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import SessionLocal, get_db
from app.services.workflow_service import WorkflowRunNotFoundError, create_weekly_workflow_run, get_workflow_run_or_raise
from app.workflows.weekly_report import (
    build_initial_weekly_report_state,
    build_weekly_report_graph_with_postgres_checkpointer,
)


logger = get_logger(__name__)
router = APIRouter(prefix="/workflows", tags=["workflows"])


def _state_to_response(state: dict) -> WeeklyWorkflowRunResponse:
    """Translate the serialized graph state into a stable API response."""
    return WeeklyWorkflowRunResponse(
        workflow_run_id=UUID(state["run_id"]),
        status=state["status"],
        human_edit_status=state.get("human_edit_status"),
        report_id=UUID(state["report_id"]) if state.get("report_id") else None,
        review_decision=state.get("review_decision"),
        exported_markdown_path=state.get("exported_markdown_path"),
    )


@router.post("/weekly-report/run", response_model=WeeklyWorkflowRunResponse, status_code=status.HTTP_201_CREATED)
def run_weekly_report_workflow(
    payload: WeeklyWorkflowRunRequest,
    db: Session = Depends(get_db),
) -> WeeklyWorkflowRunResponse:
    """
    Start a new weekly-report workflow and run until the human-edit interrupt.

    The graph itself handles the step-by-step orchestration. This API is mainly
    responsible for creating the run record and passing the initial state into
    the compiled LangGraph instance.
    """

    workflow_run = create_weekly_workflow_run(
        db,
        week_start=payload.week_start,
        week_end=payload.week_end,
    )
    initial_state = build_initial_weekly_report_state(
        run_id=str(workflow_run.id),
        week_start=payload.week_start,
        week_end=payload.week_end,
        input_document_ids=[str(document_id) for document_id in payload.input_document_ids],
    )
    config = {"configurable": {"thread_id": str(workflow_run.id)}}

    with build_weekly_report_graph_with_postgres_checkpointer(
        db_session_factory=SessionLocal,
        conn_string=settings.database_url,
    ) as graph:
        state = graph.invoke(initial_state, config=config)

    logger.info(
        "workflow.api.run_completed workflow_run_id=%s status=%s human_edit_status=%s",
        workflow_run.id,
        state["status"],
        state.get("human_edit_status"),
    )
    return _state_to_response(state)


@router.post("/{workflow_run_id}/resume", response_model=WeeklyWorkflowRunResponse)
def resume_weekly_report_workflow(
    workflow_run_id: UUID,
    db: Session = Depends(get_db),
) -> WeeklyWorkflowRunResponse:
    """
    Resume a previously interrupted weekly-report workflow from the last checkpoint.

    In the current MVP this is primarily used to continue from `human_edit` into
    `export_markdown`.
    """

    try:
        get_workflow_run_or_raise(db, workflow_run_id)
    except WorkflowRunNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    config = {"configurable": {"thread_id": str(workflow_run_id)}}
    with build_weekly_report_graph_with_postgres_checkpointer(
        db_session_factory=SessionLocal,
        conn_string=settings.database_url,
    ) as graph:
        state = graph.invoke(None, config=config)

    logger.info(
        "workflow.api.resumed workflow_run_id=%s status=%s exported_markdown_path=%s",
        workflow_run_id,
        state["status"],
        state.get("exported_markdown_path"),
    )
    return _state_to_response(state)
