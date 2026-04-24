"""add task logs table

Revision ID: 0002_add_task_logs
Revises: 0001_initial
Create Date: 2026-04-24 02:10:00
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "0002_add_task_logs"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "task_logs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("task_id", sa.String(length=36), sa.ForeignKey("rewrite_tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("level", sa.String(length=16), nullable=False),
        sa.Column("stage", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("detail", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_task_logs_task_id", "task_logs", ["task_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_task_logs_task_id", table_name="task_logs")
    op.drop_table("task_logs")
