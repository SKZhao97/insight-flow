from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.enums import WorkflowEventStatus, WorkflowStatus, WorkflowType
from app.db.models.workflow import WorkflowEvent, WorkflowRun


logger = get_logger(__name__)


class WorkflowRunNotFoundError(ValueError):
    """Raised when a workflow node references a non-existent run."""


def create_weekly_workflow_run(
    db: Session,
    *,
    week_start: datetime,
    week_end: datetime,
    state_json: dict | None = None,
) -> WorkflowRun:
    workflow_run = WorkflowRun(
        workflow_type=WorkflowType.WEEKLY_REPORT.value,
        status=WorkflowStatus.RUNNING.value,
        week_start=week_start,
        week_end=week_end,
        state_json=state_json or {},
        retry_count=0,
        started_at=datetime.now().astimezone(),
    )
    db.add(workflow_run)
    db.commit()
    db.refresh(workflow_run)
    logger.info(
        "workflow_run.created workflow_run_id=%s workflow_type=%s week_start=%s week_end=%s",
        workflow_run.id,
        workflow_run.workflow_type,
        week_start.isoformat(),
        week_end.isoformat(),
    )
    return workflow_run


def get_workflow_run_or_raise(db: Session, workflow_run_id: UUID | str) -> WorkflowRun:
    """Load a workflow run once and fail loudly if the state points to a stale identifier."""
    workflow_run = db.get(WorkflowRun, workflow_run_id)
    if workflow_run is None:
        raise WorkflowRunNotFoundError(f"workflow_run {workflow_run_id} not found")
    return workflow_run


def update_workflow_run_state(
    db: Session,
    *,
    workflow_run: WorkflowRun,
    state_json: dict,
    status: str | None = None,
    finished_at: datetime | None = None,
) -> WorkflowRun:
    """
    Persist the latest serialized graph state on every node boundary.

    The workflow row is our query-friendly mirror of the latest graph state.
    Fields like retry_count are duplicated intentionally so the operational UI
    does not need to parse JSON just to answer basic questions.
    """
    workflow_run.state_json = state_json
    workflow_run.retry_count = int(state_json.get("retry_count", 0))
    if status is not None:
        workflow_run.status = status
    if finished_at is not None:
        workflow_run.finished_at = finished_at
    db.commit()
    db.refresh(workflow_run)
    logger.info(
        "workflow_run.state_updated workflow_run_id=%s status=%s finished_at=%s",
        workflow_run.id,
        workflow_run.status,
        workflow_run.finished_at.isoformat() if workflow_run.finished_at else "-",
    )
    return workflow_run


def start_workflow_event(
    db: Session,
    *,
    workflow_run_id: UUID,
    node_name: str,
    idempotency_key: str | None = None,
    input_snapshot_ref: str | None = None,
) -> WorkflowEvent:
    """Create an explicit execution record before a workflow node starts mutating state."""
    event = WorkflowEvent(
        workflow_run_id=workflow_run_id,
        node_name=node_name,
        status=WorkflowEventStatus.STARTED.value,
        idempotency_key=idempotency_key,
        input_snapshot_ref=input_snapshot_ref,
        started_at=datetime.now().astimezone(),
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    logger.info(
        "workflow_event.started workflow_run_id=%s workflow_event_id=%s node_name=%s",
        workflow_run_id,
        event.id,
        node_name,
    )
    return event


def complete_workflow_event(
    db: Session,
    *,
    event: WorkflowEvent,
    output_snapshot_ref: str | None = None,
    status: str = WorkflowEventStatus.COMPLETED.value,
) -> WorkflowEvent:
    """Mark a workflow event as completed or intentionally skipped."""
    event.status = status
    event.output_snapshot_ref = output_snapshot_ref
    event.finished_at = datetime.now().astimezone()
    db.commit()
    db.refresh(event)
    logger.info(
        "workflow_event.completed workflow_event_id=%s node_name=%s status=%s",
        event.id,
        event.node_name,
        event.status,
    )
    return event


def fail_workflow_event(
    db: Session,
    *,
    event: WorkflowEvent,
    error_code: str,
    error_message: str,
) -> WorkflowEvent:
    """Persist failure metadata so node-level errors are queryable after the fact."""
    event.status = WorkflowEventStatus.FAILED.value
    event.error_code = error_code
    event.error_message = error_message[:2000]
    event.finished_at = datetime.now().astimezone()
    db.commit()
    db.refresh(event)
    logger.error(
        "workflow_event.failed workflow_event_id=%s node_name=%s error_code=%s error_message=%s",
        event.id,
        event.node_name,
        event.error_code,
        event.error_message,
    )
    return event
