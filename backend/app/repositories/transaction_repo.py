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
