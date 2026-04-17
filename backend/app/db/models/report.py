from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.cluster import Cluster
    from app.db.models.document import Document
    from app.db.models.summary import Summary


class Report(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "reports"
    __table_args__ = (
        Index("idx_reports_type", "type"),
        Index("idx_reports_window_start_end", "window_start", "window_end"),
        Index("idx_reports_status", "status"),
        Index("idx_reports_generated_by_run_id", "generated_by_run_id"),
    )

    type: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    content_md: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    generated_by_run_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("workflow_runs.id", ondelete="SET NULL"),
        nullable=True,
    )

    items: Mapped[list["ReportItem"]] = relationship(
        back_populates="report",
        cascade="all, delete-orphan",
    )
    edits: Mapped[list["UserEdit"]] = relationship(
        back_populates="report",
        cascade="all, delete-orphan",
    )


class ReportItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "report_items"
    __table_args__ = (
        UniqueConstraint(
            "report_id",
            "summary_id",
            "document_id",
            "position",
            name="uq_report_items_report_summary_document_position",
        ),
        Index("idx_report_items_report_id", "report_id"),
        Index("idx_report_items_summary_id", "summary_id"),
        Index("idx_report_items_document_id", "document_id"),
        Index("idx_report_items_cluster_id", "cluster_id"),
    )

    report_id: Mapped[UUID] = mapped_column(
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
    )
    summary_id: Mapped[UUID] = mapped_column(
        ForeignKey("summaries.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    cluster_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("clusters.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    item_type: Mapped[str] = mapped_column(String(32), nullable=False)
    position: Mapped[int] = mapped_column(Integer, nullable=False)

    report: Mapped["Report"] = relationship(back_populates="items")
    summary: Mapped["Summary"] = relationship()
    document: Mapped["Document"] = relationship()
    cluster: Mapped["Cluster | None"] = relationship()


class UserEdit(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "user_edits"
    __table_args__ = (Index("idx_user_edits_report_id", "report_id"),)

    report_id: Mapped[UUID] = mapped_column(
        ForeignKey("reports.id", ondelete="CASCADE"),
        nullable=False,
    )
    editor_type: Mapped[str] = mapped_column(String(32), nullable=False, default="human")
    before_content: Mapped[str] = mapped_column(Text, nullable=False)
    after_content: Mapped[str] = mapped_column(Text, nullable=False)
    edit_summary: Mapped[str | None] = mapped_column(Text)

    report: Mapped["Report"] = relationship(back_populates="edits")
