from __future__ import annotations

"""Read-oriented workflow-run queries for the frontend workbench."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.workflow import WorkflowRun


def list_workflow_runs(db: Session) -> list[WorkflowRun]:
    """Return workflow runs ordered by creation time for operational visibility."""
    stmt = select(WorkflowRun).order_by(WorkflowRun.created_at.desc())
    return list(db.scalars(stmt).all())
