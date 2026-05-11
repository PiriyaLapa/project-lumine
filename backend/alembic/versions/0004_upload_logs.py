"""upload_logs table

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-11

Records every SAP file upload attempt.
Used by GET /api/v1/upload/history (manager-only) and
duplicate date-range detection on POST /api/v1/upload.
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "upload_logs",
        sa.Column("id", sa.Integer, primary_key=True, index=True),
        sa.Column("store_id", sa.Integer, sa.ForeignKey("stores.id"), nullable=False, index=True),
        sa.Column("staff_id", sa.Integer, sa.ForeignKey("staff.id"), nullable=False, index=True),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("uploaded_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("row_count", sa.Integer, nullable=False),
        sa.Column("tasks_created", sa.Integer, nullable=False),
        sa.Column("date_range_start", sa.Date, nullable=False),
        sa.Column("date_range_end", sa.Date, nullable=False),
        sa.Column("status", sa.String(20), nullable=False),  # success | error
    )


def downgrade() -> None:
    op.drop_table("upload_logs")
