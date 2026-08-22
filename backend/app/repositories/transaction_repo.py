"""
Transaction Repository — all Transaction DB queries live here.
No raw SQL — SQLAlchemy ORM only.
"""
import logging
from sqlalchemy.orm import Session

from app.models.transaction import Transaction

logger = logging.getLogger(__name__)


def get_by_idoc(db: Session, idoc_number: str) -> Transaction | None:
    return db.query(Transaction).filter(Transaction.idoc_number == idoc_number).first()


def create(db: Session, data: dict) -> Transaction:
    """Insert a single validated transaction. Returns ORM instance."""
    transaction = Transaction(**data)
    db.add(transaction)
    db.flush()
    logger.info("transaction_repo: created idoc=%s customer=%s", data["idoc_number"], data["customer_id"])
    return transaction


def upsert(db: Session, data: dict) -> tuple[Transaction, bool]:
    """
    Insert or update a transaction by idoc_number.
    On conflict: updates sales_rep_name only (backfill use case — PK unchanged).
    Returns (transaction, created) — created=False means existing row was updated.
    """
    existing = get_by_idoc(db, data["idoc_number"])
    if existing:
        existing.sales_rep_name = data.get("sales_rep_name")
        existing.customer_name = data.get("customer_name")
        db.flush()
        logger.info("transaction_repo: upserted idoc=%s (backfill sales_rep_name, customer_name)", data["idoc_number"])
        return existing, False
    transaction = Transaction(**data)
    db.add(transaction)
    db.flush()
    logger.info("transaction_repo: created idoc=%s customer=%s", data["idoc_number"], data["customer_id"])
    return transaction, True


def get_by_customer_in_store(db: Session, customer_id: str, store_id: int) -> list[Transaction]:
    """
    Return all transactions for a customer, scoped to staff in the given store.
    Store-wide within a store — see CLAUDE.md Auth Rules exception for the
    GET /customers/{id}/* endpoints.
    """
    from app.models.staff import Staff

    return (
        db.query(Transaction)
        .join(Staff, Transaction.staff_id == Staff.id)
        .filter(
            Transaction.customer_id == customer_id,
            Staff.store_id == store_id,
            Staff.deleted_at.is_(None),
        )
        .order_by(Transaction.posting_date.desc())
        .all()
    )


def create_many(db: Session, records: list[dict]) -> list[Transaction]:
    """
    Bulk-insert transactions from SAPParser output.
    Skips duplicates (idoc_number already exists).
    Returns list of newly created Transaction instances.
    """
    created = []
    for record in records:
        existing = get_by_idoc(db, record["idoc_number"])
        if existing:
            logger.info("transaction_repo: skipping duplicate idoc=%s", record["idoc_number"])
            continue
        created.append(create(db, record))
    return created
