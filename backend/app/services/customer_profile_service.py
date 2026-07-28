"""
Customer Profile Service — assembles the read-only Customer Profile view
(GET /api/v1/customers/{customer_id}) used by the Customer Profile screen.

Falls back to transaction data when no `customers` row exists — SAP-only
customers who were never CRM-imported or self-registered (see migration
0006_unified_customer.py docstring). Never includes phone/email/line_id —
those remain restricted per CLAUDE.md's contact-PII rule.
"""
from sqlalchemy.orm import Session

from app.repositories import customer_repo, transaction_repo


def get_profile(db: Session, customer_id: str, store_id: int) -> dict | None:
    """
    Returns a profile dict, or None if the customer has no transactions in
    the requester's store — the router turns that into a 404 without
    leaking whether the customer exists in another store.
    """
    transactions = transaction_repo.get_by_customer_in_store(db, customer_id, store_id)
    if not transactions:
        return None

    customer = customer_repo.get_by_id(db, customer_id)
    if customer:
        return {
            "customer_id": customer.customer_id,
            "name": customer.name,
            "do_not_contact": customer.do_not_contact,
            "source": customer.source,
            "created_at": str(customer.created_at),
            "updated_at": str(customer.updated_at),
        }

    created_ats = [t.created_at for t in transactions]
    return {
        "customer_id": customer_id,
        "name": transactions[0].customer_name,
        "do_not_contact": False,
        "source": "sap_only",
        "created_at": str(min(created_ats)),
        "updated_at": str(max(created_ats)),
    }
