"""
Reports Router — GET /api/v1/reports/kpi, GET /api/v1/reports/dashboard
SRS §5 FR-06 multi-staff isolation:
  - sales_associate → own KPI (staff_id from JWT)
  - store_manager   → store-wide KPI (store_id from JWT)
"""
import logging
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_staff
from app.services.auth_service import TokenPayload
from app.services.dashboard_service import DashboardService
from app.services.report_service import ReportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["reports"])


class KPIReport(BaseModel):
    staff_id: Optional[int]
    store_id: int
    total_tasks: int
    completed_tasks: int
    completion_rate: float


@router.get("/reports/kpi", response_model=KPIReport)
def get_kpi(
    db: Session = Depends(get_db),
    current_staff: TokenPayload = Depends(get_current_staff),
):
    """
    Return KPI report.
    store_manager: aggregate across all active staff in their store.
    sales_associate: their own tasks only.
    """
    if current_staff.role == "store_manager":
        result = ReportService.get_kpi_for_store(db=db, store_id=current_staff.store_id)
    else:
        result = ReportService.get_kpi_for_staff(
            db=db,
            staff_id=current_staff.staff_id,
            store_id=current_staff.store_id,
        )

    return KPIReport(
        staff_id=result.staff_id,
        store_id=result.store_id,
        total_tasks=result.total_tasks,
        completed_tasks=result.completed_tasks,
        completion_rate=result.completion_rate,
    )


class StaffFollowUpStats(BaseModel):
    staff_id: Optional[int]
    staff_name: Optional[str]
    tasks_due: int
    tasks_done: int
    tasks_pending: int
    tasks_skipped: int
    messages_sent_line: int
    messages_sent_email: int
    customers_followed_up: int


class ManagerDashboardReport(BaseModel):
    store_id: int
    period: str
    date_from: Optional[date]
    date_to: Optional[date]
    staff_breakdown: list[StaffFollowUpStats]
    store_totals: StaffFollowUpStats


@router.get("/reports/dashboard", response_model=ManagerDashboardReport)
def get_dashboard(
    period: str = Query(default="today", pattern="^(today|week|month|all)$"),
    db: Session = Depends(get_db),
    current_staff: TokenPayload = Depends(get_current_staff),
):
    """
    Follow-Up Dashboard — every role sees their own follow-up performance.
    store_manager: per-staff breakdown across all active staff in their store.
    sales_associate: their own single-row stats (same shape, one-item breakdown).
    """
    if current_staff.role == "store_manager":
        result = DashboardService.get_manager_dashboard(
            db=db, store_id=current_staff.store_id, period=period
        )
    else:
        result = DashboardService.get_staff_dashboard(
            db=db, staff_id=current_staff.staff_id, store_id=current_staff.store_id, period=period
        )

    return ManagerDashboardReport(
        store_id=result.store_id,
        period=result.period,
        date_from=result.date_from,
        date_to=result.date_to,
        staff_breakdown=[StaffFollowUpStats(**vars(s)) for s in result.staff_breakdown],
        store_totals=StaffFollowUpStats(**vars(result.store_totals)),
    )
