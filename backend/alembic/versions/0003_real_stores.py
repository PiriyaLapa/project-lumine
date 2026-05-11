"""Replace placeholder store with real Hugo Boss Thailand stores

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-26

1. Migrate existing staff (store_id=1) to store_id=8901 before deleting old store.
2. Delete placeholder store id=1.
3. Insert 5 real Hugo Boss Thailand store locations.
"""
from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None

REAL_STORES = [
    (8901, "BOSS Siam Paragon"),
    (8902, "BOSS Central Chidlom"),
    (8904, "BOSS Icon Siam"),
    (8907, "BOSS Emporium"),
    (8918, "BOSS One Bangkok"),
]


def upgrade() -> None:
    # 1. Insert real stores first — FK requires target to exist before staff is updated
    for store_id, name in REAL_STORES:
        op.execute(f"INSERT INTO stores (id, name) VALUES ({store_id}, '{name}')")

    # 2. Move existing staff off placeholder store (now store 8901 exists)
    op.execute("UPDATE staff SET store_id = 8901 WHERE store_id = 1")

    # 3. Remove placeholder store — no staff references it anymore
    op.execute("DELETE FROM stores WHERE id = 1")


def downgrade() -> None:
    for store_id, _ in REAL_STORES:
        op.execute(f"DELETE FROM stores WHERE id = {store_id}")
    op.execute("INSERT INTO stores (id, name) VALUES (1, 'Hugo Boss Thailand')")
    op.execute("UPDATE staff SET store_id = 1 WHERE store_id = 8901")
