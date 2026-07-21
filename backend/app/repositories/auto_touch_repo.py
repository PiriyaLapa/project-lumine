"""
Auto-Touch Repository — today-list, status summary, skip tracking, and
message logging. do_not_contact and skipped_until exclusion are enforced
here in the WHERE clause — never left to the service/router (SEC-3).
"""
import logging
from datetime import date, timedelta

from sqlalchemy import case
from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.models.follow_up_task import FollowUpTask
from app.models.message import Message
from app.models.transaction import Transaction

logger = logging.getLogger(__name__)

_TASK_TYPE_ORDER = case(
    (FollowUpTask.task_type == "2D", 0),
    (FollowUpTask.task_type == "2W", 1),
    (FollowUpTask.task_type == "2M", 2),
    else_=3,
)


def get_today_list(db: Session, staff_id: int) -> list[tuple]:
    """
    Return (FollowUpTask, Transaction, Customer) tuples due today or
    overdue for this staff member. Excludes do_not_contact customers and
    tasks currently deferred by a skip. Overdue first, then 2D->2W->2M.
    """
    today = date.today()
    is_overdue = case((FollowUpTask.due_date < today, 0), else_=1)

    return (
        db.query(FollowUpTask, Transaction, Customer)
        .join(Transaction, FollowUpTask.idoc_number == Transaction.idoc_number)
        .join(Customer, Transaction.customer_id == Customer.customer_id)
        .filter(
            Transaction.staff_id == staff_id,
            FollowUpTask.status == "Pending",
            FollowUpTask.due_date <= today,
            Customer.do_not_contact.is_(False),
            (FollowUpTask.skipped_until.is_(None)) | (FollowUpTask.skipped_until < today),
        )
        .order_by(is_overdue, _TASK_TYPE_ORDER, FollowUpTask.due_date.asc())
        .all()
    )


def get_status_summary(db: Session, staff_id: int) -> dict:
    """Aggregate today's due/sent/pending/skipped counts for this staff member."""
    today = date.today()

    total_due = (
        db.query(FollowUpTask)
        .join(Transaction, FollowUpTask.idoc_number == Transaction.idoc_number)
        .filter(Transaction.staff_id == staff_id, FollowUpTask.due_date <= today)
        .count()
    )
    pending = (
        db.query(FollowUpTask)
        .join(Transaction, FollowUpTask.idoc_number == Transaction.idoc_number)
        .filter(
            Transaction.staff_id == staff_id,
            FollowUpTask.status == "Pending",
            FollowUpTask.due_date <= today,
            (FollowUpTask.skipped_until.is_(None)) | (FollowUpTask.skipped_until < today),
        )
        .count()
    )
    skipped = (
        db.query(FollowUpTask)
        .join(Transaction, FollowUpTask.idoc_number == Transaction.idoc_number)
        .filter(
            Transaction.staff_id == staff_id,
            FollowUpTask.skipped_until.is_not(None),
            FollowUpTask.skipped_until >= today,
        )
        .count()
    )
    sent = (
        db.query(Message)
        .filter(Message.staff_id == staff_id, Message.created_at >= today)
        .count()
    )

    return {"date": today, "total_due": total_due, "sent": sent, "pending": pending, "skipped": skipped}


def record_skip(db: Session, task: FollowUpTask) -> date:
    """Defer a task to tomorrow. Returns the deferred_to date."""
    deferred_to = date.today() + timedelta(days=1)
    task.skipped_until = deferred_to
    db.flush()
    logger.info("auto_touch_repo: skipped task_id=%s until=%s", task.id, deferred_to)
    return deferred_to


def create_message(db: Session, data: dict) -> Message:
    """Insert a send-attempt row into messages."""
    message = Message(**data)
    db.add(message)
    db.flush()
    logger.info("auto_touch_repo: created message customer_id=%s task_id=%s", data.get("customer_id"), data.get("task_id"))
    return message


def get_pending_task_for_customer(db: Session, customer_id: str, staff_id: int) -> tuple | None:
    """
    Resolve the single pending task for this customer+staff, for the
    skip endpoint (no task_id in the request — per the 2-2-2 model a
    customer should have at most one due task at a time; earliest
    due_date wins if that assumption is ever violated).
    """
    return (
        db.query(FollowUpTask, Transaction, Customer)
        .join(Transaction, FollowUpTask.idoc_number == Transaction.idoc_number)
        .join(Customer, Transaction.customer_id == Customer.customer_id)
        .filter(
            Transaction.customer_id == customer_id,
            Transaction.staff_id == staff_id,
            FollowUpTask.status == "Pending",
        )
        .order_by(FollowUpTask.due_date.asc())
        .first()
    )


def get_task_with_customer(db: Session, task_id: int) -> tuple | None:
    """Return (FollowUpTask, Transaction, Customer) for a single task, or None."""
    return (
        db.query(FollowUpTask, Transaction, Customer)
        .join(Transaction, FollowUpTask.idoc_number == Transaction.idoc_number)
        .join(Customer, Transaction.customer_id == Customer.customer_id)
        .filter(FollowUpTask.id == task_id)
        .first()
    )
