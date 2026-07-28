"""
Customers Router — POST /api/v1/customers/import-crm,
POST /api/v1/customers/register, and the Customer Profile read endpoints
(GET .../{customer_id}, .../transactions, .../tasks).
Field names locked to openapi.yaml.
"""
import logging
from datetime import date as date_type
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
from app.services import customer_profile_service
from app.repositories import task_repo, transaction_repo

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


class CustomerProfileResponse(BaseModel):
    """Customer Profile view — no phone/email/line_id (contact PII restricted)."""

    customer_id: str  # LOCKED
    name: str
    do_not_contact: bool  # LOCKED
    source: str
    created_at: str
    updated_at: str


class CustomerTransactionResponse(BaseModel):
    idoc_number: str
    posting_date: date_type
    material_desc: str | None = None
    price: float | None = None
    returned: bool
    staff_name: str | None = None

    model_config = {"from_attributes": True}


class CustomerTaskResponse(BaseModel):
    """Mirrors FollowUpTaskResponse in routers/tasks.py — field names locked to openapi.yaml."""

    id: int
    customer_id: str  # LOCKED
    task_type: str  # LOCKED: 2D | 2W | 2M
    task_basis: str  # LOCKED: posting_date | manual_override
    due_date: date_type  # LOCKED
    calculated_from: date_type  # LOCKED
    status: str  # LOCKED: Pending | Done | Superseded
    staff_name: str | None = None
    customer_name: str | None = None
    created_at: str
    updated_at: str


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


@router.get("/customers/{customer_id}", response_model=CustomerProfileResponse)
def get_customer_profile(
    customer_id: str,
    db: Session = Depends(get_db),
    current_staff: TokenPayload = Depends(get_current_staff),
):
    """
    Customer Profile identity — name only, never phone/email/line_id.
    Store-wide within the requester's store (see CLAUDE.md Auth Rules
    exception). 404 if the customer has no transactions in this store,
    to avoid leaking cross-store customer existence.
    """
    profile = customer_profile_service.get_profile(db, customer_id, current_staff.store_id)
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Customer not found.")
    return profile


@router.get("/customers/{customer_id}/transactions", response_model=list[CustomerTransactionResponse])
def get_customer_transactions(
    customer_id: str,
    db: Session = Depends(get_db),
    current_staff: TokenPayload = Depends(get_current_staff),
):
    """Purchase history — store-wide within the requester's store."""
    transactions = transaction_repo.get_by_customer_in_store(db, customer_id, current_staff.store_id)
    return [
        CustomerTransactionResponse(
            idoc_number=t.idoc_number,
            posting_date=t.posting_date,
            material_desc=t.material_desc,
            price=t.price,
            returned=t.returned,
            staff_name=t.sales_rep_name,
        )
        for t in transactions
    ]


@router.get("/customers/{customer_id}/tasks", response_model=list[CustomerTaskResponse])
def get_customer_tasks(
    customer_id: str,
    db: Session = Depends(get_db),
    current_staff: TokenPayload = Depends(get_current_staff),
):
    """Follow-up history (all statuses: Pending/Done/Superseded) — store-wide within the requester's store."""
    rows = task_repo.get_all_by_customer_in_store(db, customer_id, current_staff.store_id)
    return [
        CustomerTaskResponse(
            id=t.id,
            customer_id=t.customer_id,
            task_type=t.task_type,
            task_basis=t.task_basis,
            due_date=t.due_date,
            calculated_from=t.calculated_from,
            status=t.status,
            staff_name=staff_name,
            customer_name=customer_name,
            created_at=str(t.created_at),
            updated_at=str(t.updated_at),
        )
        for t, staff_name, customer_name in rows
    ]
