"""
Customer Repository — all Customer DB queries live here.
No raw SQL — SQLAlchemy ORM only.

get_contactable_by_id is the only lookup Auto-Touch code should use —
it enforces do_not_contact=False at the WHERE clause (never rely on the
router/service to filter this out after the fact).
"""
import logging
import uuid
from sqlalchemy.orm import Session

from app.models.customer import Customer

logger = logging.getLogger(__name__)


def get_by_id(db: Session, customer_id: str) -> Customer | None:
    """Admin/import lookup — returns the row regardless of do_not_contact."""
    return db.query(Customer).filter(Customer.customer_id == customer_id).first()


def get_contactable_by_id(db: Session, customer_id: str) -> Customer | None:
    """Auto-Touch lookup — returns None if do_not_contact=True."""
    return (
        db.query(Customer)
        .filter(Customer.customer_id == customer_id, Customer.do_not_contact.is_(False))
        .first()
    )


def create(db: Session, data: dict) -> Customer:
    """Insert a new customer (CRM import path). Returns ORM instance."""
    customer = Customer(**data)
    db.add(customer)
    db.flush()
    logger.info("customer_repo: created customer_id=%s source=%s", data["customer_id"], data.get("source"))
    return customer


def register(db: Session, data: dict) -> Customer:
    """Insert a new customer via manual point-of-sale registration."""
    data = {**data, "source": "manual_registration"}
    customer = Customer(**data)
    db.add(customer)
    db.flush()
    logger.info("customer_repo: registered customer_id=%s", data["customer_id"])
    return customer


def update_contact_info(
    db: Session, customer: Customer, phone: str | None = None, email: str | None = None, line_id: str | None = None
) -> Customer:
    """Update contact fields only — never touches name/language/do_not_contact."""
    if phone is not None:
        customer.phone = phone
    if email is not None:
        customer.email = email
    if line_id is not None:
        customer.line_id = line_id
    db.flush()
    return customer


def assign_temp_id(db: Session) -> str:
    """
    Generate a unique 'TMP-' prefixed customer_id for registrations without
    a known SAP customer_id. UUID-based to avoid race conditions under
    concurrent registration (no query-then-insert window).
    """
    return f"TMP-{uuid.uuid4().hex[:8]}"
