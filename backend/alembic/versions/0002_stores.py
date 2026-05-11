"""stores table and FK from staff.store_id

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-26

1. Creates stores table (id, name).
2. Seeds store id=1 before adding FK — existing staff rows reference store_id=1.
3. Adds FK constraint staff.store_id → stores.id.
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stores",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("name", sa.String(200), nullable=False),
    )

    # Seed before FK constraint — staff rows already have store_id=1
    op.execute("INSERT INTO stores (id, name) VALUES (1, 'Hugo Boss Thailand')")

    op.create_foreign_key(
        "fk_staff_store_id",
        "staff",
        "stores",
        ["store_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_staff_store_id", "staff", type_="foreignkey")
    op.drop_table("stores")
