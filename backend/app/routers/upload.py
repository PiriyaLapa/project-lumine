"""
Upload Router — POST /api/v1/upload
SAP file → SAPParser (Rule 7) → transaction_repo → CycleReset → response.
"""
import logging
from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_staff
from app.services.auth_service import TokenPayload
from app.services.sap_parser import SAPParser, SAPParseError
from app.services.cycle_reset import CycleReset
from app.repositories import staff_repo, transaction_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["upload"])


class UploadResponse(BaseModel):
    tasks_created: int
    customers_processed: int
    cycles_reset: int
    errors: list[str]


@router.post("/upload", response_model=UploadResponse)
async def upload_sap_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_staff: TokenPayload = Depends(get_current_staff),
):
    """
    Upload a SAP CSV/Excel file.
    Only processes rows matching this staff member's employee_code.
    Rule 7: all data passes through SAPParser before touching MySQL.
    """
    # Look up staff's employee_code (needed by SAPParser filter)
    staff = staff_repo.get_by_id(db, current_staff.staff_id)
    if not staff:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Staff not found.")

    # Read file bytes
    contents = await file.read()
    file_buffer = BytesIO(contents)
    filename = file.filename or "upload.csv"

    # Parse (Rule 7 enforced inside SAPParser)
    try:
        parser = SAPParser(staff_employee_code=staff.employee_code)
        parse_result = parser.parse(file_buffer, filename=filename)
    except SAPParseError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error_code": "SAP_PARSE_ERROR", "message": str(exc), "detail": ""},
        )

    # Process each parsed record
    tasks_created_total = 0
    cycles_reset_total = 0
    customers_processed = set()

    try:
        for record in parse_result.records:
            # Insert transaction (skip duplicate idoc_numbers)
            transaction = transaction_repo.create(db, {
                "idoc_number": record["idoc_number"],
                "posting_date": record["posting_date"],
                "customer_id": record["customer_id"],
                "staff_id": current_staff.staff_id,
                "ean": record.get("ean"),
                "material_desc": record.get("material_desc"),
            })

            # Run Cycle Reset (supersedes old Pending tasks + creates fresh 2-2-2)
            reset_result = CycleReset.run(db, transaction)
            tasks_created_total += reset_result.tasks_created
            cycles_reset_total += reset_result.cycles_reset
            customers_processed.add(record["customer_id"])

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
