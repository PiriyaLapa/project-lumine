"""
Store Repository — all Store DB queries live here.
Services and routers call this. Never touch DB directly.
No raw SQL — SQLAlchemy ORM only.
"""
import logging
from sqlalchemy.orm import Session

from app.models.store import Store

logger = logging.getLogger(__name__)


def get_all(db: Session) -> list[Store]:
    """Return all stores ordered by id."""
    return db.query(Store).order_by(Store.id).all()
