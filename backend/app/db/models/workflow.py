from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class WorkflowRun(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "workflow_runs"
    __table_args__ = (
        Index("idx_workflow_runs_type", "workflow_type"),
        Index("idx_workflow_runs_status", "status"),
        Index("idx_workflow_runs_week_start_end", "week_start", "week_end"),
    )

    workflow_type: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    week_start: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    week_end: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    state_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    events: Mapped[list["WorkflowEvent"]] = relationship(
        back_populates="workflow_run",
        cascade="all, delete-orphan",
    )
    retrieval_records: Mapped[list["RetrievalRecord"]] = relationship(
        back_populates="workflow_run",
        cascade="all, delete-orphan",
    )
    context_packs: Mapped[list["ContextPack"]] = relationship(
        back_populates="workflow_run",
        cascade="all, delete-orphan",
    )


class WorkflowEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "workflow_events"
    __table_args__ = (
        Index("idx_workflow_events_run_id", "workflow_run_id"),
        Index("idx_workflow_events_node_name", "node_name"),
        Index("idx_workflow_events_status", "status"),
    )

    workflow_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("workflow_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    node_name: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(255))
    input_snapshot_ref: Mapped[str | None] = mapped_column(String(255))
    output_snapshot_ref: Mapped[str | None] = mapped_column(String(255))
    error_code: Mapped[str | None] = mapped_column(String(128))
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    workflow_run: Mapped["WorkflowRun"] = relationship(back_populates="events")


class RetrievalRecord(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "retrieval_records"
    __table_args__ = (Index("idx_retrieval_records_workflow_run_id", "workflow_run_id"),)

    workflow_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("workflow_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    filter_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    retrieved_summary_ids: Mapped[list[UUID] | None] = mapped_column(ARRAY(PGUUID(as_uuid=True)))
    retrieved_chunk_ids: Mapped[list[UUID] | None] = mapped_column(ARRAY(PGUUID(as_uuid=True)))
    score_snapshot: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    workflow_run: Mapped["WorkflowRun"] = relationship(back_populates="retrieval_records")


class ContextPack(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "context_packs"
    __table_args__ = (Index("idx_context_packs_workflow_run_id", "workflow_run_id"),)

    workflow_run_id: Mapped[UUID] = mapped_column(
        ForeignKey("workflow_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    context_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    build_version: Mapped[str] = mapped_column(String(64), nullable=False)

    workflow_run: Mapped["WorkflowRun"] = relationship(back_populates="context_packs")

