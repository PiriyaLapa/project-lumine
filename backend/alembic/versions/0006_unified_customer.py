"""Add customers table (unified customer record)

Revision ID: 0006
Revises: 0005
Create Date: 2026-07-21

Unifies customer identity across three sources: SAP transactions,
CRM Excel import, and manual point-of-sale registration (source column).
No FK from transactions.customer_id — the join is query-time only,
since transactions.customer_id predates this table and isn't guaranteed
to match a customers row (SAP-only customers may never be imported/registered).
staff_id is nullable — SAP-only customers have no registering staff.
phone/email are PII — never log.
"""
from alembic import op
import sqlalchemy as sa

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customers",
        sa.Column("customer_id", sa.String(50), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("phone", sa.String(20), nullable=True),  # PII — never log
        sa.Column("email", sa.String(255), nullable=True),  # PII — never log
        sa.Column("line_id", sa.String(100), nullable=True),
        sa.Column("language", sa.String(5), nullable=False, server_default="th"),  # th | en
        sa.Column(
            "language_source", sa.String(20), nullable=False, server_default="auto_detected"
        ),  # auto_detected | manual_override
        sa.Column("do_not_contact", sa.Boolean, nullable=False, server_default=sa.false()),
        sa.Column(
            "source", sa.String(30), nullable=False, server_default="crm_import"
        ),  # crm_import | manual_registration | sap_only
        sa.Column("staff_id", sa.Integer, sa.ForeignKey("staff.id"), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_customers_do_not_contact", "customers", ["do_not_contact"])


def downgrade() -> None:
    op.drop_index("ix_customers_do_not_contact", table_name="customers")
    op.drop_table("customers")
