from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.db.models.document import Document
    from app.db.models.workflow import WorkflowRun


class Cluster(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "clusters"
    __table_args__ = (
        Index("idx_clusters_workflow_run_id", "workflow_run_id"),
        Index("idx_clusters_window_start_end", "window_start", "window_end"),
        Index("idx_clusters_cluster_type", "cluster_type"),
        Index("idx_clusters_status", "status"),
    )

    workflow_run_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("workflow_runs.id", ondelete="CASCADE"),
        nullable=True,
    )
    title: Mapped[str] = mapped_column(Text, nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    cluster_type: Mapped[str] = mapped_column(String(32), nullable=False)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    window_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    build_version: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)

    items: Mapped[list["ClusterItem"]] = relationship(
        back_populates="cluster",
        cascade="all, delete-orphan",
    )
    workflow_run: Mapped["WorkflowRun | None"] = relationship()


class ClusterItem(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "cluster_items"
    __table_args__ = (
        UniqueConstraint("cluster_id", "document_id", name="uq_cluster_items_cluster_document"),
        Index("idx_cluster_items_cluster_id", "cluster_id"),
        Index("idx_cluster_items_document_id", "document_id"),
    )

    cluster_id: Mapped[UUID] = mapped_column(
        ForeignKey("clusters.id", ondelete="CASCADE"),
        nullable=False,
    )
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    position: Mapped[int | None] = mapped_column(Integer)

    cluster: Mapped["Cluster"] = relationship(back_populates="items")
    document: Mapped["Document"] = relationship()
