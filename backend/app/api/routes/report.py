from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.schemas.report import ReportDetail, ReportItemView, ReportListItem, ReportTraceItem, ReportTraceResponse
from app.core.logging import get_logger
from app.db.session import get_db
from app.services.report_service import get_report, list_reports


logger = get_logger(__name__)
router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("", response_model=list[ReportListItem])
def get_reports(db: Session = Depends(get_db)) -> list[ReportListItem]:
    reports = list_reports(db)
    logger.info("reports.list returned_count=%s", len(reports))
    return [ReportListItem.model_validate(report) for report in reports]


@router.get("/{report_id}", response_model=ReportDetail)
def get_report_detail(
    report_id: UUID,
    db: Session = Depends(get_db),
) -> ReportDetail:
    report = get_report(db, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"report {report_id} not found")

    return ReportDetail(
        id=report.id,
        type=report.type,
        title=report.title,
        window_start=report.window_start,
        window_end=report.window_end,
        content_md=report.content_md,
        status=report.status,
        version=report.version,
        generated_by_run_id=report.generated_by_run_id,
        created_at=report.created_at,
        updated_at=report.updated_at,
        items=[ReportItemView.model_validate(item) for item in sorted(report.items, key=lambda item: item.position)],
    )


@router.get("/{report_id}/markdown")
def download_report_markdown(
    report_id: UUID,
    db: Session = Depends(get_db),
) -> Response:
    """Return the persisted report markdown as a downloadable text payload."""
    report = get_report(db, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"report {report_id} not found")

    filename = f"report-{report.window_start:%Y%m%d}-{report.id}.md"
    logger.info("reports.download_markdown report_id=%s filename=%s", report.id, filename)
    return Response(
        content=report.content_md,
        media_type="text/markdown; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{report_id}/trace", response_model=ReportTraceResponse)
def get_report_trace(
    report_id: UUID,
    db: Session = Depends(get_db),
) -> ReportTraceResponse:
    """
    Return the explicit citation chain for one report.

    This endpoint makes report provenance inspectable without forcing clients to
    reconstruct the trace from multiple tables on their own.
    """

    report = get_report(db, report_id)
    if report is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"report {report_id} not found")

    items = []
    for item in sorted(report.items, key=lambda item: item.position):
        items.append(
            ReportTraceItem(
                id=item.id,
                position=item.position,
                item_type=item.item_type,
                source_url=item.source_url,
                cluster_id=item.cluster_id,
                document_id=item.document_id,
                document_title=item.document.title,
                summary_id=item.summary_id,
                summary_text=item.summary.short_summary,
            )
        )

    logger.info("reports.trace report_id=%s item_count=%s", report.id, len(items))
    return ReportTraceResponse(
        report_id=report.id,
        title=report.title,
        generated_by_run_id=report.generated_by_run_id,
        items=items,
    )
