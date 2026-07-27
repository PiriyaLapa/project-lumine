"""Add messages table (Auto-Touch send log)

Revision ID: 0007
Revises: 0006
Create Date: 2026-07-21

Records every Auto-Touch send attempt (LINE and/or Email), one row per
send call. task_id is nullable — reserved for future non-task messages,
but Sprint 1 always sets it. message_text is the final sent text
(possibly associate-edited from the AI draft), not the draft itself.
"""
from alembic import op
import sqlalchemy as sa

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "customer_id",
            sa.String(50),
            sa.ForeignKey("customers.customer_id"),
            nullable=False,
            index=True,
        ),
        sa.Column("staff_id", sa.Integer, sa.ForeignKey("staff.id"), nullable=False, index=True),
        sa.Column(
            "task_id", sa.Integer, sa.ForeignKey("follow_up_tasks.id"), nullable=True, index=True
        ),
        sa.Column("touchpoint_type", sa.String(5), nullable=True),  # 2D | 2W | 2M
        sa.Column("message_text", sa.Text, nullable=False),
        sa.Column("channel_line", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("channel_email", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column("status_line", sa.String(20), nullable=True),  # sent | failed | not_available
        sa.Column("status_email", sa.String(20), nullable=True),  # sent | failed | not_available
        sa.Column("sent_at", sa.DateTime, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("messages")
