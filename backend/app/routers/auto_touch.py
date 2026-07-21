"""
Auto-Touch Router — 6 endpoints: today, generate-message, send, skip,
status. Field names locked to openapi.yaml.
"""
import logging
from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_staff
from app.services.auth_service import TokenPayload
from app.services.auto_touch_service import AutoTouchService, AutoTouchOwnershipError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["auto-touch"])


# ---------------------------------------------------------------------------
# Schemas — field names locked to openapi.yaml
# ---------------------------------------------------------------------------

class AutoTouchProduct(BaseModel):
    product_raw: str
    product_clean: str
    price: float | None = None
    returned: bool


class AutoTouchCustomer(BaseModel):
    customer_id: str  # LOCKED
    customer_name: str
    language: str
    task_id: int  # LOCKED
    task_type: str
    due_date: date
    days_since_purchase: int
    products: list[AutoTouchProduct]
    channels_available: dict
    send_status: str  # LOCKED


class GenerateMessageRequest(BaseModel):
    customer_id: str
    task_id: int


class GenerateMessageResponse(BaseModel):
    message_text: str
    language: str
    touchpoint: str


class SendMessageRequest(BaseModel):
    task_id: int
    message_text: str
    channels: list[str] | None = None

    @field_validator("message_text")
    @classmethod
    def not_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("message_text must not be empty")
        return v


class SendMessageResponse(BaseModel):
    customer_id: str
    task_id: int
    channels_sent: list[str]
    sent_at: datetime
    status: str


class SkipResponse(BaseModel):
    customer_id: str
    task_id: int
    deferred_to: date


class AutoTouchStatusResponse(BaseModel):
    date: date
    total_due: int
    sent: int
    pending: int
    skipped: int


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/auto-touch/today", response_model=list[AutoTouchCustomer])
def get_today_list(
    db: Session = Depends(get_db),
    current_staff: TokenPayload = Depends(get_current_staff),
):
    service = AutoTouchService()
    return service.get_today_list(db, current_staff.staff_id)


@router.post("/auto-touch/generate-message", response_model=GenerateMessageResponse)
def generate_message(
    body: GenerateMessageRequest,
    db: Session = Depends(get_db),
    current_staff: TokenPayload = Depends(get_current_staff),
):
    try:
        service = AutoTouchService()
        result = service.generate_message(db, body.customer_id, body.task_id, current_staff.staff_id)
    except AutoTouchOwnershipError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return GenerateMessageResponse(
        message_text=result.message_text, language=result.language, touchpoint=result.touchpoint
    )


@router.post("/auto-touch/send/{customer_id}", response_model=SendMessageResponse)
def send_message(
    customer_id: str,
    body: SendMessageRequest,
    db: Session = Depends(get_db),
    current_staff: TokenPayload = Depends(get_current_staff),
):
    try:
        service = AutoTouchService()
        result = service.send_message(
            db, customer_id, body.task_id, body.message_text, body.channels, current_staff.staff_id
        )
    except AutoTouchOwnershipError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))

    db.commit()
    logger.info("auto_touch.send: staff=%d task=%d status=%s", current_staff.staff_id, body.task_id, result["status"])
    return SendMessageResponse(**result)


@router.post("/auto-touch/skip/{customer_id}", response_model=SkipResponse)
def skip(
    customer_id: str,
    db: Session = Depends(get_db),
    current_staff: TokenPayload = Depends(get_current_staff),
):
    try:
        service = AutoTouchService()
        result = service.skip(db, customer_id, current_staff.staff_id)
    except AutoTouchOwnershipError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    db.commit()
    return SkipResponse(customer_id=customer_id, task_id=result["task_id"], deferred_to=result["deferred_to"])


@router.get("/auto-touch/status", response_model=AutoTouchStatusResponse)
def get_status(
    db: Session = Depends(get_db),
    current_staff: TokenPayload = Depends(get_current_staff),
):
    service = AutoTouchService()
    return service.get_status(db, current_staff.staff_id)
