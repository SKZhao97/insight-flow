from __future__ import annotations

"""Services for report export and human-edit state transitions."""

from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.db.enums import ReportStatus
from app.db.models.report import Report


logger = get_logger(__name__)


def mark_report_editing(db: Session, report: Report) -> Report:
    """
    Move a draft report into the human-edit stage without mutating its content.

    This gives the workflow a durable hand-off point: automation has finished
    drafting, but the report is not yet considered exported or finalized.
    """
    report.status = ReportStatus.EDITING.value
    db.commit()
    db.refresh(report)
    logger.info(
        "report.marked_editing report_id=%s status=%s",
        report.id,
        report.status,
    )
    return report


def export_report_markdown(db: Session, report: Report) -> str:
    """
    Persist the markdown body of a report to the configured export directory.

    The returned path becomes part of workflow state so downstream API or UI
    layers can show users exactly where the generated artifact was written.
    """
    export_dir = Path(settings.report_export_dir)
    export_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{report.window_start:%Y%m%d}_{report.id}.md"
    file_path = export_dir / filename
    file_path.write_text(report.content_md, encoding="utf-8")

    report.status = ReportStatus.EXPORTED.value
    db.commit()
    db.refresh(report)

    logger.info(
        "report.exported report_id=%s export_path=%s",
        report.id,
        file_path,
    )
    return str(file_path)
