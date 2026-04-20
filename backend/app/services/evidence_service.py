"""
Evidence Service — Google Drive upload + EvidenceLog record creation.
SRS §5 FR-04, §7 NFR-03 (PDPA), §15 (error handling).

Key rules:
- Images over 800KB are rejected with ValueError (mobile must compress first)
- Drive upload failure → image_uri=None saved, does NOT raise (task completion must not block)
- Filenames: evidence_{task_id}_{timestamp}.jpg — no customer PII
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from app.repositories import evidence_repo
from app.services import google_drive_client as drive_client
from app.config import Settings

logger = logging.getLogger(__name__)

settings = Settings()

MAX_IMAGE_SIZE_KB = settings.MAX_IMAGE_SIZE_KB


@dataclass
class EvidenceResult:
    id: int
    notes: Optional[str]
    image_uri: Optional[str]
    image_size_kb: Optional[float]
    timestamp: object   # datetime from DB record
    drive_failed: bool


class EvidenceService:

    @classmethod
    def save(
        cls,
        db,
        task_id: int,
        staff_id: int,
        notes: str,
        image_bytes: Optional[bytes],
        filename: Optional[str],
    ) -> EvidenceResult:
        """
        Save evidence for a task. Uploads image to Google Drive if provided.

        Raises:
            ValueError: if image exceeds MAX_IMAGE_SIZE_KB (800KB).
        """
        image_size_kb: Optional[float] = None
        image_uri: Optional[str] = None
        drive_failed: bool = False

        if image_bytes is not None:
            image_size_kb = len(image_bytes) / 1024

            if image_size_kb > MAX_IMAGE_SIZE_KB:
                raise ValueError(
                    f"Image size {image_size_kb:.1f}KB exceeds the {MAX_IMAGE_SIZE_KB}KB limit. "
                    "Compress on device before upload."
                )

            # PDPA-compliant filename — no customer PII, no staff name
            timestamp = int(datetime.now(timezone.utc).timestamp())
            drive_filename = f"evidence_{task_id}_{timestamp}.jpg"

            try:
                image_uri = drive_client.upload(image_bytes, drive_filename)
            except Exception as exc:
                logger.warning(
                    "Google Drive upload failed for task_id=%d: %s — saving null URI",
                    task_id,
                    exc,
                )
                image_uri = None
                drive_failed = True

        record = evidence_repo.create(
            db=db,
            task_id=task_id,
            staff_id=staff_id,
            notes=notes,
            image_uri=image_uri,
            image_size_kb=image_size_kb,
        )

        return EvidenceResult(
            id=record.id,
            notes=record.notes,
            image_uri=image_uri,
            image_size_kb=image_size_kb,
            timestamp=record.timestamp,
            drive_failed=drive_failed,
        )
