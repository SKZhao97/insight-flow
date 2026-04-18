"""workflow scoped clusters

Revision ID: 20260418_0002
Revises: 20260416_0001
Create Date: 2026-04-18 19:10:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260418_0002"
down_revision = "20260416_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "clusters",
        sa.Column("workflow_run_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index("idx_clusters_workflow_run_id", "clusters", ["workflow_run_id"], unique=False)
    op.create_foreign_key(
        op.f("fk_clusters_workflow_run_id_workflow_runs"),
        "clusters",
        "workflow_runs",
        ["workflow_run_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    op.drop_constraint(op.f("fk_clusters_workflow_run_id_workflow_runs"), "clusters", type_="foreignkey")
    op.drop_index("idx_clusters_workflow_run_id", table_name="clusters")
    op.drop_column("clusters", "workflow_run_id")
