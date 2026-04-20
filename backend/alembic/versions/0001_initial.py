"""initial

Revision ID: 0001
Revises:
Create Date: 2026-04-20

Creates all four Lumine tables:
  staff · transactions · follow_up_tasks · evidence_logs
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # staff
    # ------------------------------------------------------------------
    op.create_table(
        "staff",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("employee_code", sa.String(50), nullable=False, unique=True),
        sa.Column("role", sa.String(50), nullable=False),          # sales_associate | store_manager
        sa.Column("store_id", sa.Integer, nullable=False, index=True),
        sa.Column("email", sa.String(200), nullable=False, unique=True),
        sa.Column("hashed_password", sa.String(200), nullable=False),
        sa.Column("deleted_at", sa.DateTime, nullable=True),       # soft-delete (PDPA)
    )

    # ------------------------------------------------------------------
    # transactions
    # ------------------------------------------------------------------
    op.create_table(
        "transactions",
        sa.Column("idoc_number", sa.String(100), primary_key=True),
        sa.Column("posting_date", sa.Date, nullable=False),
        sa.Column("ean", sa.String(50), nullable=True),
        sa.Column("material_desc", sa.String(500), nullable=True),
        sa.Column("customer_id", sa.String(100), nullable=False, index=True),  # no name — PDPA
        sa.Column("staff_id", sa.Integer, sa.ForeignKey("staff.id"), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    # ------------------------------------------------------------------
    # follow_up_tasks
    # ------------------------------------------------------------------
    op.create_table(
        "follow_up_tasks",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("customer_id", sa.String(100), nullable=False, index=True),
        sa.Column(
            "idoc_number",
            sa.String(100),
            sa.ForeignKey("transactions.idoc_number"),
            nullable=False,
        ),
        sa.Column("task_type", sa.String(10), nullable=False),     # 2D | 2W | 2M
        sa.Column("task_basis", sa.String(20), nullable=False, server_default="posting_date"),
        sa.Column("due_date", sa.Date, nullable=False),
        sa.Column("calculated_from", sa.Date, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="Pending"),  # Pending | Done | Superseded
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )

    # ------------------------------------------------------------------
    # evidence_logs
    # ------------------------------------------------------------------
    op.create_table(
        "evidence_logs",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column(
            "task_id",
            sa.Integer,
            sa.ForeignKey("follow_up_tasks.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("notes", sa.String(2000), nullable=True),
        sa.Column("image_uri", sa.String(500), nullable=True),     # null if Drive upload failed
        sa.Column("image_size_kb", sa.Integer, nullable=True),
        sa.Column("timestamp", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("staff_id", sa.Integer, sa.ForeignKey("staff.id"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("evidence_logs")
    op.drop_table("follow_up_tasks")
    op.drop_table("transactions")
    op.drop_table("staff")
