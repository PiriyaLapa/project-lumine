"""
Dashboard Service — Follow-Up Dashboard calculation (all roles).
sales_associate sees their own single-row stats; store_manager sees a
per-staff breakdown across their store — both computed with the same
_stats_for_staff helper, mirroring report_service.py's staff/store split,
extended to also read the messages table for channel send counts.
"""
import logging
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Optional

from app.repositories import dashboard_repo, staff_repo

logger = logging.getLogger(__name__)


@dataclass
class StaffFollowUpStats:
    staff_id: Optional[int]
    staff_name: Optional[str]
    tasks_due: int
    tasks_done: int
    tasks_pending: int
    tasks_skipped: int
    messages_sent_line: int
    messages_sent_email: int
    customers_followed_up: int


@dataclass
class DashboardResult:
    store_id: int
    period: str
    date_from: Optional[date]
    date_to: Optional[date]
    staff_breakdown: list
    store_totals: StaffFollowUpStats


def resolve_period_range(period: str, today: date) -> tuple[Optional[date], Optional[date]]:
    """Pure function — `today` is injected so boundary tests are deterministic."""
    if period == "today":
        return today, today
    if period == "week":
        monday = today - timedelta(days=today.weekday())
        return monday, today
    if period == "month":
        return today.replace(day=1), today
    if period == "all":
        return None, None
    raise ValueError(f"Unknown period: {period}")


def _stats_for_staff(staff_id, staff_name, task_rows, message_rows) -> StaffFollowUpStats:
    my_tasks = [t for (t, sid) in task_rows if sid == staff_id]
    my_messages = [m for m in message_rows if m.staff_id == staff_id]

    tasks_pending = sum(1 for t in my_tasks if t.status == "Pending")
    tasks_done = sum(1 for t in my_tasks if t.status == "Done")
    tasks_skipped = sum(1 for t in my_tasks if t.skipped_until is not None)

    line_sent = sum(1 for m in my_messages if m.status_line == "sent")
    email_sent = sum(1 for m in my_messages if m.status_email == "sent")
    followed_up = {
        m.customer_id for m in my_messages if m.status_line == "sent" or m.status_email == "sent"
    }

    return StaffFollowUpStats(
        staff_id=staff_id,
        staff_name=staff_name,
        tasks_due=len(my_tasks),
        tasks_done=tasks_done,
        tasks_pending=tasks_pending,
        tasks_skipped=tasks_skipped,
        messages_sent_line=line_sent,
        messages_sent_email=email_sent,
        customers_followed_up=len(followed_up),
    )


def _sum_totals(rows) -> StaffFollowUpStats:
    return StaffFollowUpStats(
        staff_id=None,
        staff_name=None,
        tasks_due=sum(r.tasks_due for r in rows),
        tasks_done=sum(r.tasks_done for r in rows),
        tasks_pending=sum(r.tasks_pending for r in rows),
        tasks_skipped=sum(r.tasks_skipped for r in rows),
        messages_sent_line=sum(r.messages_sent_line for r in rows),
        messages_sent_email=sum(r.messages_sent_email for r in rows),
        customers_followed_up=sum(r.customers_followed_up for r in rows),
    )


class DashboardService:

    @classmethod
    def get_manager_dashboard(cls, db, store_id: int, period: str) -> DashboardResult:
        """Per-staff breakdown across all active staff in the manager's store."""
        date_from, date_to = resolve_period_range(period, date.today())

        staff_list = dashboard_repo.get_active_staff_for_store(db, store_id=store_id)
        task_rows = dashboard_repo.get_tasks_for_store_dashboard(db, store_id, date_from, date_to)
        message_rows = dashboard_repo.get_messages_for_store_dashboard(db, store_id, date_from, date_to)

        breakdown = [
            _stats_for_staff(staff.id, staff.name, task_rows, message_rows) for staff in staff_list
        ]
        totals = _sum_totals(breakdown)

        logger.info(
            "dashboard: store_id=%d period=%s staff_count=%d total_due=%d",
            store_id, period, len(breakdown), totals.tasks_due,
        )
        return DashboardResult(
            store_id=store_id, period=period, date_from=date_from, date_to=date_to,
            staff_breakdown=breakdown, store_totals=totals,
        )

    @classmethod
    def get_staff_dashboard(cls, db, staff_id: int, store_id: int, period: str) -> DashboardResult:
        """A single associate's own stats, in the same shape as the manager view."""
        date_from, date_to = resolve_period_range(period, date.today())

        staff = staff_repo.get_by_id(db, staff_id)
        staff_name = staff.name if staff else None
        task_rows = dashboard_repo.get_tasks_for_staff_dashboard(db, staff_id, date_from, date_to)
        message_rows = dashboard_repo.get_messages_for_staff_dashboard(db, staff_id, date_from, date_to)

        own_stats = _stats_for_staff(staff_id, staff_name, task_rows, message_rows)

        logger.info(
            "dashboard: staff_id=%d store_id=%d period=%s total_due=%d",
            staff_id, store_id, period, own_stats.tasks_due,
        )
        return DashboardResult(
            store_id=store_id, period=period, date_from=date_from, date_to=date_to,
            staff_breakdown=[own_stats], store_totals=own_stats,
        )
