"""Add index on follow_up_tasks.idoc_number

Revision ID: 0011
Revises: 0010
Create Date: 2026-08-15

The FK side of the follow_up_tasks -> transactions join had no index
(unlike the sibling customer_id column), forcing a scan of
follow_up_tasks on every join. get_status_summary() runs 4 such joins
per call, making it disproportionately expensive relative to get_tasks'
single equivalent join — a contributing factor to Dashboard load
failures under concurrent request load.
"""
from alembic import op

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_follow_up_tasks_idoc_number", "follow_up_tasks", ["idoc_number"])


def downgrade() -> None:
    op.drop_index("ix_follow_up_tasks_idoc_number", table_name="follow_up_tasks")
