from __future__ import annotations

"""Read-oriented report queries for the frontend workbench."""

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.report import Report, ReportItem


def list_reports(db: Session) -> list[Report]:
    """Return reports ordered by recency for the workbench list page."""
    stmt = select(Report).order_by(Report.window_start.desc(), Report.created_at.desc())
    return list(db.scalars(stmt).all())


def get_report(db: Session, report_id) -> Report | None:
    """Load one report together with its report items for the editor/detail page."""
    stmt = (
        select(Report)
        .where(Report.id == report_id)
        .options(
            selectinload(Report.items).selectinload(ReportItem.summary),
            selectinload(Report.items).selectinload(ReportItem.document),
        )
    )
    return db.scalar(stmt)
