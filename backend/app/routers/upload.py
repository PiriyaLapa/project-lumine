"""
Upload Router — POST /api/v1/upload and GET /api/v1/upload/history.
SAP file → SAPParser (Rule 7) → overlap check → transaction_repo → CycleReset → upload_log_repo → response.
"""
import logging
from datetime import date, datetime
from io import BytesIO
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_staff
from app.services.auth_service import TokenPayload
from app.services.sap_parser import SAPParser, SAPParseError
from app.services.cycle_reset import CycleReset
from app.repositories import staff_repo, transaction_repo, upload_log_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["upload"])


# ---------------------------------------------------------------------------
# Response schemas — field names locked to openapi.yaml
# ---------------------------------------------------------------------------

class UploadResponse(BaseModel):
    tasks_created: int
    customers_processed: int
    cycles_reset: int
    errors: list[str]


class UploadLogResponse(BaseModel):
    id: int
    store_id: int
    staff_id: int
    filename: str
    uploaded_at: datetime
    row_count: int
    tasks_created: int
    date_range_start: date
    date_range_end: date
    status: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/upload", response_model=UploadResponse)
async def upload_sap_file(
    file: UploadFile = File(...),
    force: bool = Query(default=False),
    db: Session = Depends(get_db),
    current_staff: TokenPayload = Depends(get_current_staff),
):
    """
    Upload a SAP CSV/Excel file.
    Only processes rows matching this staff member's employee_code.
    Rule 7: all data passes through SAPParser before touching MySQL.
    ?force=true bypasses duplicate date-range detection.
    """
    staff = staff_repo.get_by_id(db, current_staff.staff_id)
    if not staff:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Staff not found.")

    contents = await file.read()
    file_buffer = BytesIO(contents)
    filename = file.filename or "upload.csv"

    try:
        parser = SAPParser(staff_employee_code=staff.employee_code)
        parse_result = parser.parse(file_buffer, filename=filename)
    except SAPParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "SAP_PARSE_ERROR", "message": str(exc), "detail": ""},
        )

    # Derive date range and check for overlap (skipped when records are empty)
    date_range_start: Optional[date] = None
    date_range_end: Optional[date] = None

    if parse_result.records:
        posting_dates = [r["posting_date"] for r in parse_result.records]
        date_range_start = min(posting_dates)
        date_range_end = max(posting_dates)

        if not force:
            overlap = upload_log_repo.find_overlap(
                db,
                store_id=current_staff.store_id,
                start=date_range_start,
                end=date_range_end,
            )
            if overlap:
                return JSONResponse(
                    status_code=status.HTTP_409_CONFLICT,
                    content={
                        "conflict": True,
                        "overlapping_upload": {
                            "filename": overlap.filename,
                            "uploaded_at": overlap.uploaded_at.isoformat(),
                            "date_range": f"{overlap.date_range_start} to {overlap.date_range_end}",
                        },
                    },
                )

    tasks_created_total = 0
    cycles_reset_total = 0
    customers_processed = set()

    try:
        for record in parse_result.records:
            data = {
                "idoc_number": record["idoc_number"],
                "posting_date": record["posting_date"],
                "customer_id": record["customer_id"],
                "staff_id": current_staff.staff_id,
                "ean": record.get("ean"),
                "material_desc": record.get("material_desc"),
                "sales_rep_name": record.get("sales_rep_name"),
            }

            if force:
                transaction, created = transaction_repo.upsert(db, data)
            else:
                transaction = transaction_repo.create(db, data)
                created = True

            customers_processed.add(record["customer_id"])

            if created:
                reset_result = CycleReset.run(db, transaction)
                tasks_created_total += reset_result.tasks_created
                cycles_reset_total += reset_result.cycles_reset

        db.commit()

        if parse_result.records and date_range_start and date_range_end:
            upload_log_repo.create(
                db,
                store_id=current_staff.store_id,
                staff_id=current_staff.staff_id,
                filename=filename,
                row_count=len(parse_result.records),
                tasks_created=tasks_created_total,
                date_range_start=date_range_start,
                date_range_end=date_range_end,
                status="success",
            )
            db.commit()

        logger.info(
            "Upload complete: staff=%d customers=%d tasks=%d cycles_reset=%d errors=%d",
            current_staff.staff_id,
            len(customers_processed),
            tasks_created_total,
            cycles_reset_total,
            len(parse_result.errors),
        )
    except Exception as exc:
        db.rollback()
        logger.error("Upload failed for staff=%d: %s", current_staff.staff_id, exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error_code": "UPLOAD_FAILED", "message": "Upload failed. Please try again.", "detail": ""},
        )

    return UploadResponse(
        tasks_created=tasks_created_total,
        customers_processed=len(customers_processed),
        cycles_reset=cycles_reset_total,
        errors=parse_result.errors,
    )


@router.get("/upload/history", response_model=list[UploadLogResponse])
def get_upload_history(
    db: Session = Depends(get_db),
    current_staff: TokenPayload = Depends(get_current_staff),
):
    """
    Return upload history for the manager's store, newest first.
    store_manager role required.
    """
    if current_staff.role != "store_manager":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Manager role required.",
        )

    logs = upload_log_repo.get_by_store(db, store_id=current_staff.store_id)
    return logs
