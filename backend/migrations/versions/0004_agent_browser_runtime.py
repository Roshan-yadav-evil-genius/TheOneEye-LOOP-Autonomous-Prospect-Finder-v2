"""agent subagent state and consecutive failures

Revision ID: 0004_agent_browser_runtime
Revises: 7dbbba5fabce
Create Date: 2026-07-18
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0004_agent_browser_runtime"
down_revision = "7dbbba5fabce"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_subagent_state",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("parent_thread_id", sa.String(length=512), nullable=False),
        sa.Column("active_subagent_threads", sa.JSON(), nullable=False),
    )
    op.create_index(
        "ix_agent_subagent_state_parent_thread_id",
        "agent_subagent_state",
        ["parent_thread_id"],
        unique=True,
    )
    with op.batch_alter_table("agent_process_state") as batch:
        batch.add_column(
            sa.Column("consecutive_failures", sa.Integer(), nullable=False, server_default="0")
        )


def downgrade() -> None:
    with op.batch_alter_table("agent_process_state") as batch:
        batch.drop_column("consecutive_failures")
    op.drop_index("ix_agent_subagent_state_parent_thread_id", table_name="agent_subagent_state")
    op.drop_table("agent_subagent_state")
