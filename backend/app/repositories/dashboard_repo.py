"""
Dashboard Repository — Follow-Up Dashboard queries, store-wide (manager)
and staff-scoped (associate). Returns raw rows; dashboard_service.py
aggregates per-staff and computes totals (never here).
"""
from datetime import date, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.models.follow_up_task import FollowUpTask
from app.models.message import Message
from app.models.staff import Staff
from app.models.transaction import Transaction


def get_active_staff_for_store(db: Session, store_id: int) -> list[Staff]:
    """Active (non-soft-deleted) staff in this store, name-sorted — the
    roster the manager's per-staff breakdown is built from, so a staff
    member with zero follow-ups still appears as a zero row."""
    return (
        db.query(Staff)
        .filter(Staff.store_id == store_id, Staff.deleted_at.is_(None))
        .order_by(Staff.name.asc())
        .all()
    )


def get_tasks_for_store_dashboard(
    db: Session, store_id: int, date_from: Optional[date], date_to: Optional[date]
) -> list[tuple]:
    """(FollowUpTask, staff_id) tuples for all active staff in store,
    filtered on FollowUpTask.due_date within [date_from, date_to].
    None on either side means unbounded on that side (period=all)."""
    conditions = [Staff.store_id == store_id, Staff.deleted_at.is_(None)]
    if date_from is not None:
        conditions.append(FollowUpTask.due_date >= date_from)
    if date_to is not None:
        conditions.append(FollowUpTask.due_date <= date_to)
    return (
        db.query(FollowUpTask, Transaction.staff_id)
        .join(Transaction, Transaction.idoc_number == FollowUpTask.idoc_number)
        .join(Staff, Staff.id == Transaction.staff_id)
        .filter(*conditions)
        .all()
    )


def get_messages_for_store_dashboard(
    db: Session, store_id: int, date_from: Optional[date], date_to: Optional[date]
) -> list[Message]:
    """Message rows for all active staff in store, filtered on
    Message.created_at within [date_from, date_to] (end-of-day inclusive)."""
    conditions = [Staff.store_id == store_id, Staff.deleted_at.is_(None)]
    if date_from is not None:
        conditions.append(Message.created_at >= date_from)
    if date_to is not None:
        conditions.append(Message.created_at < date_to + timedelta(days=1))
    return (
        db.query(Message)
        .join(Staff, Staff.id == Message.staff_id)
        .filter(*conditions)
        .all()
    )


def get_tasks_for_staff_dashboard(
    db: Session, staff_id: int, date_from: Optional[date], date_to: Optional[date]
) -> list[tuple]:
    """(FollowUpTask, staff_id) tuples for a single staff member — the
    staff-scoped sibling of get_tasks_for_store_dashboard."""
    conditions = [Transaction.staff_id == staff_id]
    if date_from is not None:
        conditions.append(FollowUpTask.due_date >= date_from)
    if date_to is not None:
        conditions.append(FollowUpTask.due_date <= date_to)
    return (
        db.query(FollowUpTask, Transaction.staff_id)
        .join(Transaction, Transaction.idoc_number == FollowUpTask.idoc_number)
        .filter(*conditions)
        .all()
    )


def get_messages_for_staff_dashboard(
    db: Session, staff_id: int, date_from: Optional[date], date_to: Optional[date]
) -> list[Message]:
    """Message rows for a single staff member — the staff-scoped sibling
    of get_messages_for_store_dashboard."""
    conditions = [Message.staff_id == staff_id]
    if date_from is not None:
        conditions.append(Message.created_at >= date_from)
    if date_to is not None:
        conditions.append(Message.created_at < date_to + timedelta(days=1))
    return db.query(Message).filter(*conditions).all()
