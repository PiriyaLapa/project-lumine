"""Add price and returned to transactions (Auto-Touch product context)

Revision ID: 0009
Revises: 0008
Create Date: 2026-07-21

Auto-Touch's today-list and message-generation context need per-product
price and return status, which the transactions table never captured.
price is nullable — older rows uploaded before this migration have no
price data. returned defaults False — sap_parser.py and
sap_column_map.json must be updated separately to populate both fields
going forward instead of discarding them during parsing.
"""
from alembic import op
import sqlalchemy as sa

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "transactions",
        sa.Column("price", sa.Numeric(10, 2), nullable=True),
    )
    op.add_column(
        "transactions",
        sa.Column("returned", sa.Boolean, nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    op.drop_column("transactions", "returned")
    op.drop_column("transactions", "price")
