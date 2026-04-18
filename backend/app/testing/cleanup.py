from __future__ import annotations

"""Helpers for cleaning demo and test data from the shared development database."""

from dataclasses import dataclass, field
from pathlib import Path
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.orm import Session, sessionmaker

from app.db.base import Base
from app.db.models.cluster import Cluster
from app.db.models.document import Document
from app.db.models.report import Report
from app.db.models.source import Source
from app.db.models.workflow import WorkflowRun


@dataclass(slots=True)
class TestDataTracker:
    """Track created resources so scripts and tests can clean up after themselves."""

    document_ids: set[UUID] = field(default_factory=set)
    source_ids: set[UUID] = field(default_factory=set)
    workflow_run_ids: set[UUID] = field(default_factory=set)
    report_ids: set[UUID] = field(default_factory=set)
    file_paths: set[str] = field(default_factory=set)

    def track_document(self, document_id: UUID) -> None:
        self.document_ids.add(document_id)

    def track_source(self, source_id: UUID) -> None:
        self.source_ids.add(source_id)

    def track_workflow_run(self, workflow_run_id: UUID) -> None:
        self.workflow_run_ids.add(workflow_run_id)

    def track_report(self, report_id: UUID) -> None:
        self.report_ids.add(report_id)

    def track_file(self, file_path: str | None) -> None:
        if file_path:
            self.file_paths.add(file_path)

    def cleanup(
        self,
        *,
        session_factory: sessionmaker[Session],
        delete_files: bool = True,
    ) -> None:
        """Delete tracked entities in a dependency-safe order."""

        with session_factory() as db:
            if self.report_ids:
                db.execute(delete(Report).where(Report.id.in_(self.report_ids)))
            if self.workflow_run_ids:
                db.execute(delete(Report).where(Report.generated_by_run_id.in_(self.workflow_run_ids)))
                db.execute(delete(Cluster).where(Cluster.workflow_run_id.in_(self.workflow_run_ids)))
                db.execute(delete(WorkflowRun).where(WorkflowRun.id.in_(self.workflow_run_ids)))
            if self.document_ids:
                db.execute(delete(Document).where(Document.id.in_(self.document_ids)))
            if self.source_ids:
                db.execute(delete(Source).where(Source.id.in_(self.source_ids)))
            db.commit()

        if delete_files:
            for file_path in self.file_paths:
                path = Path(file_path)
                if path.exists():
                    path.unlink()


def reset_application_data(
    *,
    session_factory: sessionmaker[Session],
    delete_runtime_files: bool = False,
) -> None:
    """
    Delete all application rows for integration tests and demo validation runs.

    Insight Flow's dedup and retrieval logic operates across the whole database,
    so even a single leaked document from an earlier failed script can change
    later test outcomes. Integration tests therefore need a full reset of the
    shared development database before they execute.
    """

    with session_factory() as db:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()

    if delete_runtime_files:
        for root in (Path("runtime_exports/reports"), Path("runtime_exports/validation")):
            if not root.exists():
                continue
            for file_path in root.iterdir():
                if file_path.is_file():
                    file_path.unlink()
