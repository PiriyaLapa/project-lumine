"""
Upload Log Repository — all UploadLog DB operations.
Services call these; no SQL in routers or services.
"""
from datetime import date
from typing import Optional

from sqlalchemy.orm import Session

from app.models.upload_log import UploadLog


def create(
    db: Session,
    store_id: int,
    staff_id: int,
    filename: str,
    row_count: int,
    tasks_created: int,
    date_range_start: date,
    date_range_end: date,
    status: str,
) -> UploadLog:
    """Insert a new UploadLog record. Returns the saved ORM instance."""
    record = UploadLog(
        store_id=store_id,
        staff_id=staff_id,
        filename=filename,
        row_count=row_count,
        tasks_created=tasks_created,
        date_range_start=date_range_start,
        date_range_end=date_range_end,
        status=status,
    )
    db.add(record)
    db.flush()  # assigns PK without committing — caller commits
    return record


def get_by_store(db: Session, store_id: int) -> list[UploadLog]:
    """Return all upload logs for a store, newest first."""
    return (
        db.query(UploadLog)
        .filter(UploadLog.store_id == store_id)
        .order_by(UploadLog.uploaded_at.desc())
        .all()
    )


def find_overlap(
    db: Session,
    store_id: int,
    start: date,
    end: date,
    exclude_id: Optional[int] = None,
) -> Optional[UploadLog]:
    """
    Return the first existing UploadLog for this store whose date range
    overlaps [start, end], or None if no overlap exists.

    Overlap condition: existing.start <= end AND existing.end >= start
    """
    query = (
        db.query(UploadLog)
        .filter(
            UploadLog.store_id == store_id,
            UploadLog.status == "success",
            UploadLog.date_range_start <= end,
            UploadLog.date_range_end >= start,
        )
    )
    if exclude_id is not None:
        query = query.filter(UploadLog.id != exclude_id)
    return query.first()
