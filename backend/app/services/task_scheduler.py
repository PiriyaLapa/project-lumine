"""
Task Scheduler Service — 2-2-2 date calculation and task creation.
SRS §5 FR-02: task_basis is ALWAYS posting_date. Never call date, never any other date.
Due dates are never adjusted for weekends or holidays — display as-is.
"""
import logging
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.repositories import task_repo

logger = logging.getLogger(__name__)

# Fixed offsets — SRS §5 FR-02. Do not change without architect approval.
_OFFSETS = {
    "2D": timedelta(days=2),
    "2W": timedelta(days=14),
    "2M": timedelta(days=60),
}


@dataclass
class ScheduleResult:
    tasks_created: int


class TaskScheduler:
    """
    Stateless service — all methods are class methods.
    Calculates due dates from posting_date and writes tasks via task_repo.
    """

    @staticmethod
    def calculate_due_dates(posting_date: date) -> dict:
        """
        Return due date for each task type plus task_basis metadata.

        SRS rules:
        - T is always posting_date. Never call date. Never any other date.
        - timedelta handles leap years automatically (no special case needed).
        - No weekend/holiday adjustment — display due date as-is.
        """
        return {
            "2D": posting_date + _OFFSETS["2D"],
            "2W": posting_date + _OFFSETS["2W"],
            "2M": posting_date + _OFFSETS["2M"],
            "task_basis": "posting_date",
            "calculated_from": posting_date,
        }

    @classmethod
    def schedule(cls, db: Session, transaction) -> ScheduleResult:
        """
        Create 3 FollowUpTask records for a transaction.
        Called after a new Transaction is inserted (Rule 7 already enforced).

        Returns ScheduleResult with tasks_created count.
        """
        dates = cls.calculate_due_dates(transaction.posting_date)

        tasks = [
            {
                "customer_id": transaction.customer_id,
                "idoc_number": transaction.idoc_number,
                "task_type": task_type,
                "task_basis": dates["task_basis"],
                "due_date": dates[task_type],
                "calculated_from": dates["calculated_from"],
                "status": "Pending",
            }
            for task_type in ("2D", "2W", "2M")
        ]

        task_repo.create_tasks(db, tasks)

        logger.info(
            "Scheduled 3 tasks for customer=%s idoc=%s posting=%s",
            transaction.customer_id,
            transaction.idoc_number,
            transaction.posting_date,
        )

        return ScheduleResult(tasks_created=3)
