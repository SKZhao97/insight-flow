from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Index, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import EmbeddingVector

if TYPE_CHECKING:
    from app.db.models.document import Document


class Summary(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "summaries"
    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "prompt_version",
            "model_name",
            name="uq_summaries_document_prompt_model",
        ),
        Index("idx_summaries_document_id", "document_id"),
        Index("idx_summaries_category", "category"),
        Index("idx_summaries_quality_score", "quality_score"),
    )

    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    short_summary: Mapped[str] = mapped_column(Text, nullable=False)
    key_points: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    tags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    category: Mapped[str] = mapped_column(String(64), nullable=False)
    bilingual_terms: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    quality_score: Mapped[int | None] = mapped_column(SmallInteger)
    prompt_version: Mapped[str] = mapped_column(String(64), nullable=False)
    model_name: Mapped[str] = mapped_column(String(128), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)

    document: Mapped["Document"] = relationship(back_populates="summaries")
    embeddings: Mapped[list["SummaryEmbedding"]] = relationship(
        back_populates="summary",
        cascade="all, delete-orphan",
    )


class SummaryEmbedding(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "summary_embeddings"
    __table_args__ = (
        UniqueConstraint(
            "summary_id",
            "embedding_model",
            "embedding_source",
            name="uq_summary_embeddings_summary_model_source",
        ),
        Index("idx_summary_embeddings_summary_id", "summary_id"),
    )

    summary_id: Mapped[UUID] = mapped_column(
        ForeignKey("summaries.id", ondelete="CASCADE"),
        nullable=False,
    )
    embedding_model: Mapped[str] = mapped_column(String(128), nullable=False)
    embedding_source: Mapped[str] = mapped_column(String(64), nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(EmbeddingVector)

    summary: Mapped["Summary"] = relationship(back_populates="embeddings")
