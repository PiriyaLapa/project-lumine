"""Add sales_rep_name to transactions table

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-12

Stores the SAP display name (column "Sales Rep.name") alongside the
numeric staff_id FK. Avoids a Staff JOIN on every task list query.
Nullable — rows uploaded before this migration have no name stored.
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "transactions",
        sa.Column("sales_rep_name", sa.String(255), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("transactions", "sales_rep_name")
