"""
Reports Router — GET /api/v1/reports/kpi
SRS §5 FR-06 multi-staff isolation:
  - sales_associate → own KPI (staff_id from JWT)
  - store_manager   → store-wide KPI (store_id from JWT)
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_staff
from app.services.auth_service import TokenPayload
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
