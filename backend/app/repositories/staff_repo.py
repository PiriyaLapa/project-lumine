"""
Staff Repository — all Staff DB queries live here.
Services call this. Services never touch DB directly.
No raw SQL — SQLAlchemy ORM only.
"""
import logging
from sqlalchemy.orm import Session

from app.models.staff import Staff

logger = logging.getLogger(__name__)


def get_by_email(db: Session, email: str) -> Staff | None:
    """Return active staff by email, or None if not found / soft-deleted."""
    return (
        db.query(Staff)
        .filter(Staff.email == email, Staff.deleted_at.is_(None))
        .first()
    )


def get_by_id(db: Session, staff_id: int) -> Staff | None:
    """Return active staff by primary key, or None if not found / soft-deleted."""
    return (
        db.query(Staff)
        .filter(Staff.id == staff_id, Staff.deleted_at.is_(None))
        .first()
    )


def create_staff(
    db: Session,
    *,
    name: str,
    email: str,
    hashed_password: str,
    role: str,
    store_id: int,
    employee_code: str,
) -> Staff:
    """Insert a new staff record and return the saved instance."""
    staff = Staff(
        name=name,
        email=email,
        hashed_password=hashed_password,
        role=role,
        store_id=store_id,
        employee_code=employee_code,
    )
    db.add(staff)
    db.commit()
    db.refresh(staff)
    return staff


def get_by_employee_code(db: Session, employee_code: str) -> Staff | None:
    """Return active staff by SAP employee_code."""
    return (
        db.query(Staff)
        .filter(Staff.employee_code == employee_code, Staff.deleted_at.is_(None))
        .first()
    )
