from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin
from app.db.types import EmbeddingVector

if TYPE_CHECKING:
    from app.db.models.source import Source
    from app.db.models.summary import Summary


class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "documents"
    __table_args__ = (
        Index("idx_documents_source_id", "source_id"),
        Index("idx_documents_published_at", "published_at"),
        Index("idx_documents_status", "status"),
        Index("idx_documents_content_hash", "content_hash"),
        Index("idx_documents_canonical_url", "canonical_url"),
        Index("idx_documents_quality_status", "quality_status"),
        Index("idx_documents_dedup_status", "dedup_status"),
        Index(
            "idx_documents_quality_dedup_published_at",
            "quality_status",
            "dedup_status",
            "published_at",
        ),
    )

    source_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("sources.id", ondelete="SET NULL"),
        nullable=True,
    )
    ingest_type: Mapped[str] = mapped_column(String(32), nullable=False)
    url: Mapped[str | None] = mapped_column(Text)
    canonical_url: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    author: Mapped[str | None] = mapped_column(String(255))
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    language: Mapped[str | None] = mapped_column(String(16))
    raw_content: Mapped[str | None] = mapped_column(Text)
    cleaned_content: Mapped[str | None] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    extraction_method: Mapped[str] = mapped_column(String(64), nullable=False)
    quality_status: Mapped[str] = mapped_column(String(32), nullable=False)
    dedup_status: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)

    source: Mapped["Source | None"] = relationship(back_populates="documents")
    summaries: Mapped[list["Summary"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )
    chunks: Mapped[list["DocumentChunk"]] = relationship(
        back_populates="document",
        cascade="all, delete-orphan",
    )


class DocumentRelation(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "document_relations"
    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "related_document_id",
            "relation_type",
            name="uq_document_relations_document_related_relation",
        ),
        Index("idx_document_relations_document_id", "document_id"),
        Index("idx_document_relations_related_document_id", "related_document_id"),
        Index("idx_document_relations_relation_type", "relation_type"),
    )

    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    related_document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    relation_type: Mapped[str] = mapped_column(String(32), nullable=False)
    similarity_score: Mapped[float] = mapped_column(Float, nullable=False)


class DocumentChunk(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "document_chunks"
    __table_args__ = (
        UniqueConstraint(
            "document_id",
            "chunk_index",
            "embedding_model",
            name="uq_document_chunks_document_chunk_model",
        ),
        Index("idx_document_chunks_document_id", "document_id"),
        Index("idx_document_chunks_chunk_index", "chunk_index"),
    )

    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    chunk_text: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding_model: Mapped[str] = mapped_column(String(128), nullable=False)
    embedding: Mapped[list[float] | None] = mapped_column(EmbeddingVector)

    document: Mapped["Document"] = relationship(back_populates="chunks")
