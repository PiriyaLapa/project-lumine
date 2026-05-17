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


def get_by_task_id(db: Session, task_id: int) -> Optional[EvidenceLog]:
    """Return the most recent evidence log for a task, or None."""
    return (
        db.query(EvidenceLog)
        .filter(EvidenceLog.task_id == task_id)
        .order_by(EvidenceLog.id.desc())
        .first()
    )


def get_by_id(db: Session, evidence_id: int) -> Optional[EvidenceLog]:
    """Return a single evidence log by its own PK, or None."""
    return db.query(EvidenceLog).filter(EvidenceLog.id == evidence_id).first()


def update(
    db: Session,
    evidence_id: int,
    notes: Optional[str],
    image_uri: Optional[str],
    image_size_kb: Optional[float],
) -> EvidenceLog:
    """Update notes and/or image fields on an existing evidence log. Caller commits."""
    record = get_by_id(db, evidence_id)
    if notes is not None:
        record.notes = notes
    if image_uri is not None:
        record.image_uri = image_uri
        record.image_size_kb = image_size_kb
    db.flush()
    return record
