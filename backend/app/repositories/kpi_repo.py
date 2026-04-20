"""
KPI repository — task queries scoped for KPI calculation.
Returns all FollowUpTask records (including Superseded) for a staff member or store.
The service layer handles the Superseded-exclusion logic.
"""
from sqlalchemy.orm import Session

from app.models.follow_up_task import FollowUpTask
from app.models.transaction import Transaction
from app.models.staff import Staff


def get_tasks_for_staff_kpi(db: Session, staff_id: int) -> list:
    """All tasks linked to this staff member (via Transaction.staff_id)."""
    return (
        db.query(FollowUpTask)
        .join(Transaction, Transaction.idoc_number == FollowUpTask.idoc_number)
        .filter(Transaction.staff_id == staff_id)
        .all()
    )


def get_tasks_for_store_kpi(db: Session, store_id: int) -> list:
    """All tasks linked to any active staff member in this store."""
    return (
        db.query(FollowUpTask)
        .join(Transaction, Transaction.idoc_number == FollowUpTask.idoc_number)
        .join(Staff, Staff.id == Transaction.staff_id)
        .filter(Staff.store_id == store_id, Staff.deleted_at.is_(None))
        .all()
    )
