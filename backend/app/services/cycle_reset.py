"""
Cycle Reset Service — SRS §5 FR-03.
When a customer makes a new purchase:
  1. Supersede all their Pending tasks
  2. Create a fresh 2-2-2 cycle from the new posting_date

Order matters: supersede BEFORE schedule — never have both old and new Pending simultaneously.
Only Pending tasks are superseded. Done tasks are archived and excluded from KPI.
"""
import logging
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.repositories import task_repo
from app.services.task_scheduler import TaskScheduler

logger = logging.getLogger(__name__)


@dataclass
class ResetResult:
    tasks_superseded: int
    tasks_created: int
    cycles_reset: int  # 0 = first purchase, 1 = existing cycle was reset


class CycleReset:
    """Stateless service — all methods are class methods."""

    @classmethod
    def run(cls, db: Session, transaction) -> ResetResult:
        """
        Execute the Cycle Reset for a new transaction.

        Args:
            db: SQLAlchemy session
            transaction: Transaction ORM instance (already validated by SAPParser)

        Returns:
            ResetResult with counts for logging/response
        """
        # Step 1 — find existing Pending tasks for this customer
        pending = task_repo.get_pending_by_customer(db, transaction.customer_id)

        tasks_superseded = 0
        cycles_reset = 0

        if pending:
            pending_ids = [t.id for t in pending]
            tasks_superseded = task_repo.supersede_tasks(db, pending_ids)
            cycles_reset = 1
            logger.info(
                "Cycle Reset: superseded %d tasks for customer=%s",
                tasks_superseded,
                transaction.customer_id,
            )

        # Step 2 — create fresh 2-2-2 cycle from new posting_date
        schedule_result = TaskScheduler.schedule(db, transaction)

        logger.info(
            "Cycle Reset complete: customer=%s superseded=%d created=%d",
            transaction.customer_id,
            tasks_superseded,
            schedule_result.tasks_created,
        )

        return ResetResult(
            tasks_superseded=tasks_superseded,
            tasks_created=schedule_result.tasks_created,
            cycles_reset=cycles_reset,
        )
