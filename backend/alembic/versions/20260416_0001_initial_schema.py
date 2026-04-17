"""initial schema

Revision ID: 20260416_0001
Revises:
Create Date: 2026-04-16 22:10:00

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "20260416_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "sources",
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("config_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sources")),
    )
    op.create_index("idx_sources_status", "sources", ["status"], unique=False)
    op.create_index("idx_sources_type", "sources", ["type"], unique=False)

    op.create_table(
        "workflow_runs",
        sa.Column("workflow_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=64), nullable=False),
        sa.Column("week_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("week_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("state_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_workflow_runs")),
    )
    op.create_index("idx_workflow_runs_status", "workflow_runs", ["status"], unique=False)
    op.create_index("idx_workflow_runs_type", "workflow_runs", ["workflow_type"], unique=False)
    op.create_index("idx_workflow_runs_week_start_end", "workflow_runs", ["week_start", "week_end"], unique=False)

    op.create_table(
        "clusters",
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("cluster_type", sa.String(length=32), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("build_version", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_clusters")),
    )
    op.create_index("idx_clusters_cluster_type", "clusters", ["cluster_type"], unique=False)
    op.create_index("idx_clusters_status", "clusters", ["status"], unique=False)
    op.create_index("idx_clusters_window_start_end", "clusters", ["window_start", "window_end"], unique=False)

    op.create_table(
        "documents",
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("ingest_type", sa.String(length=32), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("canonical_url", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("author", sa.String(length=255), nullable=True),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("language", sa.String(length=16), nullable=True),
        sa.Column("raw_content", sa.Text(), nullable=True),
        sa.Column("cleaned_content", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(length=128), nullable=False),
        sa.Column("extraction_method", sa.String(length=64), nullable=False),
        sa.Column("quality_status", sa.String(length=32), nullable=False),
        sa.Column("dedup_status", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["sources.id"], name=op.f("fk_documents_source_id_sources"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_documents")),
    )
    op.create_index("idx_documents_canonical_url", "documents", ["canonical_url"], unique=False)
    op.create_index("idx_documents_content_hash", "documents", ["content_hash"], unique=False)
    op.create_index("idx_documents_dedup_status", "documents", ["dedup_status"], unique=False)
    op.create_index("idx_documents_published_at", "documents", ["published_at"], unique=False)
    op.create_index("idx_documents_quality_dedup_published_at", "documents", ["quality_status", "dedup_status", "published_at"], unique=False)
    op.create_index("idx_documents_quality_status", "documents", ["quality_status"], unique=False)
    op.create_index("idx_documents_source_id", "documents", ["source_id"], unique=False)
    op.create_index("idx_documents_status", "documents", ["status"], unique=False)
    op.create_index(
        "uq_documents_canonical_url_not_null",
        "documents",
        ["canonical_url"],
        unique=True,
        postgresql_where=sa.text("canonical_url IS NOT NULL"),
    )

    op.create_table(
        "context_packs",
        sa.Column("workflow_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("context_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("build_version", sa.String(length=64), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["workflow_run_id"], ["workflow_runs.id"], name=op.f("fk_context_packs_workflow_run_id_workflow_runs"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_context_packs")),
    )
    op.create_index("idx_context_packs_workflow_run_id", "context_packs", ["workflow_run_id"], unique=False)

    op.create_table(
        "retrieval_records",
        sa.Column("workflow_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("query_text", sa.Text(), nullable=False),
        sa.Column("filter_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("retrieved_summary_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column("retrieved_chunk_ids", postgresql.ARRAY(postgresql.UUID(as_uuid=True)), nullable=True),
        sa.Column("score_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["workflow_run_id"], ["workflow_runs.id"], name=op.f("fk_retrieval_records_workflow_run_id_workflow_runs"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_retrieval_records")),
    )
    op.create_index("idx_retrieval_records_workflow_run_id", "retrieval_records", ["workflow_run_id"], unique=False)

    op.create_table(
        "workflow_events",
        sa.Column("workflow_run_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("node_name", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=True),
        sa.Column("input_snapshot_ref", sa.String(length=255), nullable=True),
        sa.Column("output_snapshot_ref", sa.String(length=255), nullable=True),
        sa.Column("error_code", sa.String(length=128), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["workflow_run_id"], ["workflow_runs.id"], name=op.f("fk_workflow_events_workflow_run_id_workflow_runs"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_workflow_events")),
    )
    op.create_index("idx_workflow_events_node_name", "workflow_events", ["node_name"], unique=False)
    op.create_index("idx_workflow_events_run_id", "workflow_events", ["workflow_run_id"], unique=False)
    op.create_index("idx_workflow_events_status", "workflow_events", ["status"], unique=False)

    op.create_table(
        "document_relations",
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("related_document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relation_type", sa.String(length=32), nullable=False),
        sa.Column("similarity_score", sa.Float(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], name=op.f("fk_document_relations_document_id_documents"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["related_document_id"], ["documents.id"], name=op.f("fk_document_relations_related_document_id_documents"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document_relations")),
        sa.UniqueConstraint("document_id", "related_document_id", "relation_type", name="uq_document_relations_document_related_relation"),
    )
    op.create_index("idx_document_relations_document_id", "document_relations", ["document_id"], unique=False)
    op.create_index("idx_document_relations_related_document_id", "document_relations", ["related_document_id"], unique=False)
    op.create_index("idx_document_relations_relation_type", "document_relations", ["relation_type"], unique=False)

    op.create_table(
        "document_chunks",
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False),
        sa.Column("embedding_model", sa.String(length=128), nullable=False),
        sa.Column("embedding", Vector(dim=1536), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], name=op.f("fk_document_chunks_document_id_documents"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document_chunks")),
        sa.UniqueConstraint("document_id", "chunk_index", "embedding_model", name="uq_document_chunks_document_chunk_model"),
    )
    op.create_index("idx_document_chunks_chunk_index", "document_chunks", ["chunk_index"], unique=False)
    op.create_index("idx_document_chunks_document_id", "document_chunks", ["document_id"], unique=False)

    op.create_table(
        "summaries",
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("short_summary", sa.Text(), nullable=False),
        sa.Column("key_points", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("tags", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("bilingual_terms", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("quality_score", sa.SmallInteger(), nullable=True),
        sa.Column("prompt_version", sa.String(length=64), nullable=False),
        sa.Column("model_name", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], name=op.f("fk_summaries_document_id_documents"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_summaries")),
        sa.UniqueConstraint("document_id", "prompt_version", "model_name", name="uq_summaries_document_prompt_model"),
    )
    op.create_index("idx_summaries_category", "summaries", ["category"], unique=False)
    op.create_index("idx_summaries_document_id", "summaries", ["document_id"], unique=False)
    op.create_index("idx_summaries_quality_score", "summaries", ["quality_score"], unique=False)
    op.create_index("gin_summaries_tags", "summaries", ["tags"], unique=False, postgresql_using="gin")

    op.create_table(
        "summary_embeddings",
        sa.Column("summary_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("embedding_model", sa.String(length=128), nullable=False),
        sa.Column("embedding_source", sa.String(length=64), nullable=False),
        sa.Column("embedding", Vector(dim=1536), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["summary_id"], ["summaries.id"], name=op.f("fk_summary_embeddings_summary_id_summaries"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_summary_embeddings")),
        sa.UniqueConstraint("summary_id", "embedding_model", "embedding_source", name="uq_summary_embeddings_summary_model_source"),
    )
    op.create_index("idx_summary_embeddings_summary_id", "summary_embeddings", ["summary_id"], unique=False)

    op.create_table(
        "cluster_items",
        sa.Column("cluster_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("position", sa.Integer(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["cluster_id"], ["clusters.id"], name=op.f("fk_cluster_items_cluster_id_clusters"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], name=op.f("fk_cluster_items_document_id_documents"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cluster_items")),
        sa.UniqueConstraint("cluster_id", "document_id", name="uq_cluster_items_cluster_document"),
    )
    op.create_index("idx_cluster_items_cluster_id", "cluster_items", ["cluster_id"], unique=False)
    op.create_index("idx_cluster_items_document_id", "cluster_items", ["document_id"], unique=False)

    op.create_table(
        "reports",
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("window_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("window_end", sa.DateTime(timezone=True), nullable=False),
        sa.Column("content_md", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("generated_by_run_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["generated_by_run_id"], ["workflow_runs.id"], name=op.f("fk_reports_generated_by_run_id_workflow_runs"), ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reports")),
    )
    op.create_index("idx_reports_generated_by_run_id", "reports", ["generated_by_run_id"], unique=False)
    op.create_index("idx_reports_status", "reports", ["status"], unique=False)
    op.create_index("idx_reports_type", "reports", ["type"], unique=False)
    op.create_index("idx_reports_window_start_end", "reports", ["window_start", "window_end"], unique=False)

    op.create_table(
        "report_items",
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("summary_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("cluster_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("item_type", sa.String(length=32), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["cluster_id"], ["clusters.id"], name=op.f("fk_report_items_cluster_id_clusters"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], name=op.f("fk_report_items_document_id_documents"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"], name=op.f("fk_report_items_report_id_reports"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["summary_id"], ["summaries.id"], name=op.f("fk_report_items_summary_id_summaries"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_report_items")),
        sa.UniqueConstraint("report_id", "summary_id", "document_id", "position", name="uq_report_items_report_summary_document_position"),
    )
    op.create_index("idx_report_items_cluster_id", "report_items", ["cluster_id"], unique=False)
    op.create_index("idx_report_items_document_id", "report_items", ["document_id"], unique=False)
    op.create_index("idx_report_items_report_id", "report_items", ["report_id"], unique=False)
    op.create_index("idx_report_items_summary_id", "report_items", ["summary_id"], unique=False)

    op.create_table(
        "user_edits",
        sa.Column("report_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("editor_type", sa.String(length=32), nullable=False),
        sa.Column("before_content", sa.Text(), nullable=False),
        sa.Column("after_content", sa.Text(), nullable=False),
        sa.Column("edit_summary", sa.Text(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"], name=op.f("fk_user_edits_report_id_reports"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_user_edits")),
    )
    op.create_index("idx_user_edits_report_id", "user_edits", ["report_id"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_user_edits_report_id", table_name="user_edits")
    op.drop_table("user_edits")
    op.drop_index("idx_report_items_summary_id", table_name="report_items")
    op.drop_index("idx_report_items_report_id", table_name="report_items")
    op.drop_index("idx_report_items_document_id", table_name="report_items")
    op.drop_index("idx_report_items_cluster_id", table_name="report_items")
    op.drop_table("report_items")
    op.drop_index("idx_reports_window_start_end", table_name="reports")
    op.drop_index("idx_reports_type", table_name="reports")
    op.drop_index("idx_reports_status", table_name="reports")
    op.drop_index("idx_reports_generated_by_run_id", table_name="reports")
    op.drop_table("reports")
    op.drop_index("idx_cluster_items_document_id", table_name="cluster_items")
    op.drop_index("idx_cluster_items_cluster_id", table_name="cluster_items")
    op.drop_table("cluster_items")
    op.drop_index("idx_summary_embeddings_summary_id", table_name="summary_embeddings")
    op.drop_table("summary_embeddings")
    op.drop_index("gin_summaries_tags", table_name="summaries")
    op.drop_index("idx_summaries_quality_score", table_name="summaries")
    op.drop_index("idx_summaries_document_id", table_name="summaries")
    op.drop_index("idx_summaries_category", table_name="summaries")
    op.drop_table("summaries")
    op.drop_index("idx_document_chunks_document_id", table_name="document_chunks")
    op.drop_index("idx_document_chunks_chunk_index", table_name="document_chunks")
    op.drop_table("document_chunks")
    op.drop_index("idx_document_relations_relation_type", table_name="document_relations")
    op.drop_index("idx_document_relations_related_document_id", table_name="document_relations")
    op.drop_index("idx_document_relations_document_id", table_name="document_relations")
    op.drop_table("document_relations")
    op.drop_index("idx_workflow_events_status", table_name="workflow_events")
    op.drop_index("idx_workflow_events_run_id", table_name="workflow_events")
    op.drop_index("idx_workflow_events_node_name", table_name="workflow_events")
    op.drop_table("workflow_events")
    op.drop_index("idx_retrieval_records_workflow_run_id", table_name="retrieval_records")
    op.drop_table("retrieval_records")
    op.drop_index("idx_context_packs_workflow_run_id", table_name="context_packs")
    op.drop_table("context_packs")
    op.drop_index("uq_documents_canonical_url_not_null", table_name="documents")
    op.drop_index("idx_documents_status", table_name="documents")
    op.drop_index("idx_documents_source_id", table_name="documents")
    op.drop_index("idx_documents_quality_status", table_name="documents")
    op.drop_index("idx_documents_quality_dedup_published_at", table_name="documents")
    op.drop_index("idx_documents_published_at", table_name="documents")
    op.drop_index("idx_documents_dedup_status", table_name="documents")
    op.drop_index("idx_documents_content_hash", table_name="documents")
    op.drop_index("idx_documents_canonical_url", table_name="documents")
    op.drop_table("documents")
    op.drop_index("idx_clusters_window_start_end", table_name="clusters")
    op.drop_index("idx_clusters_status", table_name="clusters")
    op.drop_index("idx_clusters_cluster_type", table_name="clusters")
    op.drop_table("clusters")
    op.drop_index("idx_workflow_runs_week_start_end", table_name="workflow_runs")
    op.drop_index("idx_workflow_runs_type", table_name="workflow_runs")
    op.drop_index("idx_workflow_runs_status", table_name="workflow_runs")
    op.drop_table("workflow_runs")
    op.drop_index("idx_sources_type", table_name="sources")
    op.drop_index("idx_sources_status", table_name="sources")
    op.drop_table("sources")
