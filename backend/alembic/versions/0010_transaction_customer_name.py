"""Add customer_name to transactions table

Revision ID: 0010
Revises: 0009
Create Date: 2026-07-26

Stores the SAP display name (column "Customer name") alongside the
customer_id code. Avoids a Customer JOIN on every task list query —
same reasoning as sales_rep_name (migration 0005).
Nullable — rows uploaded before this migration, or without this column
in the source file, have no name stored.
"""
from alembic import op
import sqlalchemy as sa

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "transactions",
        sa.Column("customer_name", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("transactions", "customer_name")
