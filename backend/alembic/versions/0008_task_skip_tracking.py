"""Add skipped_until to follow_up_tasks (Auto-Touch skip tracking)

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-21

Auto-Touch's "skip" action defers a customer's follow-up to tomorrow
without cancelling the underlying task. skipped_until stores the date
before which this task should be excluded from the Auto-Touch "today"
list. NULL means never skipped / not currently deferred.
Kept as a separate migration rather than amending the already-locked
0006/0007 schemas.
"""
from alembic import op
import sqlalchemy as sa

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "follow_up_tasks",
        sa.Column("skipped_until", sa.Date, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("follow_up_tasks", "skipped_until")
