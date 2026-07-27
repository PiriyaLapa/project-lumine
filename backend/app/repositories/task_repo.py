"""
Task Repository — all FollowUpTask DB queries live here.
No raw SQL — SQLAlchemy ORM only.
"""
import logging
from sqlalchemy.orm import Session

from app.models.follow_up_task import FollowUpTask

logger = logging.getLogger(__name__)


def get_pending_by_customer(db: Session, customer_id: str) -> list[FollowUpTask]:
    """Return all Pending tasks for a customer (used by Cycle Reset)."""
    return (
        db.query(FollowUpTask)
        .filter(
            FollowUpTask.customer_id == customer_id,
            FollowUpTask.status == "Pending",
        )
        .all()
    )


def get_tasks_for_staff(db: Session, staff_id: int) -> list[tuple]:
    """
    Return (FollowUpTask, sales_rep_name, customer_name) tuples for a sales associate.
    Uses transactions.sales_rep_name/customer_name — no Staff/Customer JOIN needed for display names.
    Multi-staff isolation: associates see only their own tasks (via transaction join).
    """
    from app.models.transaction import Transaction

    return (
        db.query(FollowUpTask, Transaction.sales_rep_name, Transaction.customer_name)
        .join(Transaction, FollowUpTask.idoc_number == Transaction.idoc_number)
        .filter(Transaction.staff_id == staff_id)
        .order_by(FollowUpTask.due_date.asc())
        .all()
    )


def get_tasks_for_store(db: Session, store_id: int) -> list[tuple]:
    """
    Return (FollowUpTask, sales_rep_name, customer_name) tuples for all staff under a store.
    Uses transactions.sales_rep_name/customer_name — no Staff/Customer JOIN needed for display names.
    """
    from app.models.transaction import Transaction
    from app.models.staff import Staff

    return (
        db.query(FollowUpTask, Transaction.sales_rep_name, Transaction.customer_name)
        .join(Transaction, FollowUpTask.idoc_number == Transaction.idoc_number)
        .join(Staff, Transaction.staff_id == Staff.id)
        .filter(Staff.store_id == store_id, Staff.deleted_at.is_(None))
        .order_by(FollowUpTask.due_date.asc())
        .all()
    )


def get_by_id(db: Session, task_id: int) -> FollowUpTask | None:
    return db.query(FollowUpTask).filter(FollowUpTask.id == task_id).first()


def get_staff_name_for_task(db: Session, idoc_number: str) -> str:
    """Return sales_rep_name from the transaction linked to this task."""
    from app.models.transaction import Transaction

    result = (
        db.query(Transaction.sales_rep_name)
        .filter(Transaction.idoc_number == idoc_number)
        .first()
    )
    return result[0] if result and result[0] else ""


def get_customer_name_for_task(db: Session, idoc_number: str) -> str | None:
    """Return customer_name from the transaction linked to this task."""
    from app.models.transaction import Transaction

    result = (
        db.query(Transaction.customer_name)
        .filter(Transaction.idoc_number == idoc_number)
        .first()
    )
    return result[0] if result else None


def create_tasks(db: Session, tasks: list[dict]) -> list[FollowUpTask]:
    """Bulk-insert FollowUpTask records. Returns created ORM instances."""
    orm_tasks = [FollowUpTask(**t) for t in tasks]
    db.add_all(orm_tasks)
    db.flush()  # assign IDs without committing — caller controls transaction
    logger.info("task_repo: created %d tasks", len(orm_tasks))
    return orm_tasks


def supersede_tasks(db: Session, task_ids: list[int]) -> int:
    """
    Set status=Superseded for all given task IDs.
    Returns count of rows updated.
    """
    updated = (
        db.query(FollowUpTask)
        .filter(FollowUpTask.id.in_(task_ids))
        .update({"status": "Superseded"}, synchronize_session="fetch")
    )
    logger.info("task_repo: superseded %d tasks", updated)
    return updated


def mark_done(db: Session, task_id: int) -> FollowUpTask | None:
    """Set status=Done for a single task. Returns updated task or None."""
    task = get_by_id(db, task_id)
    if task and task.status == "Pending":
        task.status = "Done"
        db.flush()
    return task
