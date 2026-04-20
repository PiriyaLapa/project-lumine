"""
Report Service — KPI calculation.
SRS §6.6: completion_rate = Done / (Pending + Done). Superseded tasks excluded.
SRS §5 FR-06: sales_associate sees own KPI; store_manager sees store-wide KPI.
"""
import logging
from dataclasses import dataclass
from typing import Optional

from app.repositories import kpi_repo

logger = logging.getLogger(__name__)


@dataclass
class KPIResult:
    staff_id: Optional[int]
    store_id: int
    total_tasks: int
    completed_tasks: int
    completion_rate: float


def _calculate(tasks, staff_id: Optional[int], store_id: int) -> KPIResult:
    """Compute KPI from a list of FollowUpTask ORM objects."""
    active = [t for t in tasks if t.status != "Superseded"]
    done = [t for t in active if t.status == "Done"]

    total = len(active)
    completed = len(done)
    rate = (completed / total) if total > 0 else 0.0

    return KPIResult(
        staff_id=staff_id,
        store_id=store_id,
        total_tasks=total,
        completed_tasks=completed,
        completion_rate=rate,
    )


class ReportService:

    @classmethod
    def get_kpi_for_staff(cls, db, staff_id: int, store_id: int) -> KPIResult:
        """KPI for a single sales associate (own tasks only)."""
        tasks = kpi_repo.get_tasks_for_staff_kpi(db, staff_id=staff_id)
        result = _calculate(tasks, staff_id=staff_id, store_id=store_id)
        logger.info(
            "KPI staff_id=%d store_id=%d total=%d done=%d rate=%.2f",
            staff_id, store_id, result.total_tasks, result.completed_tasks, result.completion_rate,
        )
        return result

    @classmethod
    def get_kpi_for_store(cls, db, store_id: int) -> KPIResult:
        """Aggregate KPI across all active staff in a store (manager view)."""
        tasks = kpi_repo.get_tasks_for_store_kpi(db, store_id=store_id)
        result = _calculate(tasks, staff_id=None, store_id=store_id)
        logger.info(
            "KPI store_id=%d total=%d done=%d rate=%.2f",
            store_id, result.total_tasks, result.completed_tasks, result.completion_rate,
        )
        return result
