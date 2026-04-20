"""
Evidence repository — all EvidenceLog DB operations.
Services call these; no SQL in routers or services.
"""
from typing import Optional
from sqlalchemy.orm import Session

from app.models.evidence_log import EvidenceLog


def create(
    db: Session,
    task_id: int,
    staff_id: int,
    notes: Optional[str],
    image_uri: Optional[str],
    image_size_kb: Optional[float],
) -> EvidenceLog:
    """Insert a new EvidenceLog record. Returns the saved ORM instance."""
    record = EvidenceLog(
        task_id=task_id,
        staff_id=staff_id,
        notes=notes,
        image_uri=image_uri,
        image_size_kb=image_size_kb,
    )
    db.add(record)
    db.flush()   # assigns PK without committing — caller commits
    return record
