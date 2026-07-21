"""
Customer Register Service — manual point-of-sale registration.
This is register, not upsert: a supplied customer_id that already
exists is rejected, not overwritten.
"""
import logging

from app.repositories import customer_repo
from app.services.language_detection import detect_language

logger = logging.getLogger(__name__)


class CustomerAlreadyExistsError(Exception):
    """Raised when a supplied customer_id already exists."""


class CustomerRegisterService:
    def register(self, db, name: str, phone: str, email: str | None, customer_id: str | None, staff_id: int):
        if customer_id is not None:
            existing = customer_repo.get_by_id(db, customer_id)
            if existing is not None:
                raise CustomerAlreadyExistsError(f"Customer ID '{customer_id}' already exists.")
        else:
            customer_id = customer_repo.assign_temp_id(db)

        customer = customer_repo.register(
            db,
            {
                "customer_id": customer_id,
                "name": name,
                "phone": phone,
                "email": email,
                "language": detect_language(name),
                "language_source": "auto_detected",
                "staff_id": staff_id,
            },
        )
        logger.info("customer_register_service: registered customer_id=%s staff_id=%d", customer_id, staff_id)
        return customer
