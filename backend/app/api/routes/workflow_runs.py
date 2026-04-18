from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.schemas.workflow_runs import WorkflowRunListItem
from app.core.logging import get_logger
from app.db.session import get_db
from app.services.workflow_run_service import list_workflow_runs


logger = get_logger(__name__)
router = APIRouter(prefix="/workflow-runs", tags=["workflow-runs"])


@router.get("", response_model=list[WorkflowRunListItem])
def get_workflow_runs(db: Session = Depends(get_db)) -> list[WorkflowRunListItem]:
    workflow_runs = list_workflow_runs(db)
    logger.info("workflow_runs.list returned_count=%s", len(workflow_runs))
    return [WorkflowRunListItem.model_validate(workflow_run) for workflow_run in workflow_runs]
