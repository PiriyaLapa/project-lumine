"""
Customers Router — POST /api/v1/customers/import-crm and
POST /api/v1/customers/register.
Field names locked to openapi.yaml.
"""
import logging
from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_staff
from app.services.auth_service import TokenPayload
from app.services.crm_import_service import CRMImportService, CRMImportError
from app.services.customer_register_service import (
    CustomerRegisterService,
    CustomerAlreadyExistsError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["customers"])


# ---------------------------------------------------------------------------
# Schemas — field names locked to openapi.yaml
# ---------------------------------------------------------------------------

class ConflictDetail(BaseModel):
    customer_id: str
    existing_name: str
    import_name: str


class CRMImportResponse(BaseModel):
    updated: int
    created: int
    conflicts: int
    conflict_details: list[ConflictDetail]


class CustomerRegisterRequest(BaseModel):
    name: str
    phone: str
    email: str | None = None
    customer_id: str | None = None

    @field_validator("name", "phone")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must not be blank")
        return v


class CustomerResponse(BaseModel):
    customer_id: str  # LOCKED
    name: str
    phone: str | None = None
    email: str | None = None
    line_id: str | None = None
    language: str  # LOCKED — th | en
    language_source: str
    do_not_contact: bool  # LOCKED
    source: str
    created_at: str
    updated_at: str

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/customers/import-crm", response_model=CRMImportResponse)
async def import_crm(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_staff: TokenPayload = Depends(get_current_staff),
):
    """Bulk-import a CRM Excel export (Customer ID, Customer Name, Phone, Email)."""
    contents = await file.read()
    filename = file.filename or "crm_export.xlsx"

    try:
        service = CRMImportService(staff_id=current_staff.staff_id)
        result = service.import_file(db, BytesIO(contents), filename)
    except CRMImportError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    db.commit()
    logger.info(
        "customers.import_crm: staff=%d updated=%d created=%d conflicts=%d",
        current_staff.staff_id,
        result.updated,
        result.created,
        result.conflicts,
    )
    return CRMImportResponse(
        updated=result.updated,
        created=result.created,
        conflicts=result.conflicts,
        conflict_details=result.conflict_details,
    )


@router.post(
    "/customers/register", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED
)
def register_customer(
    body: CustomerRegisterRequest,
    db: Session = Depends(get_db),
    current_staff: TokenPayload = Depends(get_current_staff),
):
    """Quick-register a customer at point of sale. staff_id always from JWT."""
    try:
        service = CustomerRegisterService()
        customer = service.register(
            db,
            name=body.name,
            phone=body.phone,
            email=body.email,
            customer_id=body.customer_id,
            staff_id=current_staff.staff_id,
        )
    except CustomerAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    db.commit()
    logger.info("customers.register: staff=%d customer_id=%s", current_staff.staff_id, customer.customer_id)
    return customer
