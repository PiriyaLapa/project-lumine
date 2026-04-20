"""
Evidence Router — POST /api/v1/evidence
SRS §5 FR-04: staff log evidence (notes + optional image) per task.
Image must be compressed to ≤800KB on device before upload (JPEG).
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.middleware.auth import get_current_staff
from app.services.auth_service import TokenPayload
from app.services.evidence_service import EvidenceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["evidence"])

MAX_IMAGE_BYTES = 800 * 1024  # 800KB — enforced here as safety net


class EvidenceResponse(BaseModel):
    id: int
    task_id: int
    notes: Optional[str]
    image_uri: Optional[str]
    image_size_kb: Optional[float]
    timestamp: Optional[str]


@router.post("/evidence", response_model=EvidenceResponse)
async def submit_evidence(
    task_id: int = Form(...),
    notes: str = Form(""),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_staff: TokenPayload = Depends(get_current_staff),
):
    """
    Submit evidence (notes + optional JPEG image) for a task.

    - Image must be JPEG, compressed to ≤800KB on device.
    - Drive upload failure is non-fatal: record is saved with image_uri=null.
    - staff_id is always taken from the JWT token, never from the request body.
    """
    image_bytes: Optional[bytes] = None
    filename: Optional[str] = None

    if image is not None:
        image_bytes = await image.read()
        filename = image.filename

    try:
        result = EvidenceService.save(
            db=db,
            task_id=task_id,
            staff_id=current_staff.staff_id,
            notes=notes,
            image_bytes=image_bytes,
            filename=filename,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(exc),
        )

    db.commit()

    if result.drive_failed:
        logger.warning(
            "Evidence saved for task_id=%d but Drive upload failed — image_uri=null",
            task_id,
        )

    return EvidenceResponse(
        id=result.id,
        task_id=task_id,
        notes=result.notes,
        image_uri=result.image_uri,
        image_size_kb=result.image_size_kb,
        timestamp=str(result.timestamp) if result.timestamp else None,
    )
