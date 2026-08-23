"""
TDD — customer_profile_service.py.
Assembles the GET /api/v1/customers/{customer_id} response. Falls back to
transaction data when no `customers` row exists (SAP-only customers —
see migration 0006_unified_customer.py docstring).
Written before implementation — red until the service exists.
"""
from datetime import datetime
from unittest.mock import MagicMock, patch

from app.models.customer import Customer
from app.models.transaction import Transaction


def make_customer(customer_id="C1", name="Real Customer", do_not_contact=False, source="crm_import"):
    c = MagicMock(spec=Customer)
    c.customer_id = customer_id
    c.name = name
    c.do_not_contact = do_not_contact
    c.source = source
    c.created_at = datetime(2026, 1, 1)
    c.updated_at = datetime(2026, 2, 1)
    return c


def make_transaction(customer_id="C1", customer_name="SAP Name", created_at=None):
    t = MagicMock(spec=Transaction)
    t.customer_id = customer_id
    t.customer_name = customer_name
    t.created_at = created_at or datetime(2026, 3, 1)
    return t


class TestGetProfile:
    @patch("app.services.customer_profile_service.transaction_repo")
    def test_returns_none_when_no_transactions_in_store(self, mock_txn_repo):
        from app.services import customer_profile_service

        mock_txn_repo.get_by_customer_in_store.return_value = []
        db = MagicMock()

        result = customer_profile_service.get_profile(db, "C_MISSING", store_id=1)

        assert result is None

    @patch("app.services.customer_profile_service.customer_repo")
    @patch("app.services.customer_profile_service.transaction_repo")
    def test_returns_profile_from_customer_row_when_exists(self, mock_txn_repo, mock_cust_repo):
        from app.services import customer_profile_service

        mock_txn_repo.get_by_customer_in_store.return_value = [make_transaction()]
        mock_cust_repo.get_by_id.return_value = make_customer()
        db = MagicMock()

        result = customer_profile_service.get_profile(db, "C1", store_id=1)

        assert result["customer_id"] == "C1"
        assert result["name"] == "Real Customer"
        assert result["do_not_contact"] is False
        assert result["source"] == "crm_import"
        assert "phone" not in result
        assert "email" not in result
        assert "line_id" not in result

    @patch("app.services.customer_profile_service.customer_repo")
    @patch("app.services.customer_profile_service.transaction_repo")
    def test_falls_back_to_transaction_data_when_no_customer_row(self, mock_txn_repo, mock_cust_repo):
        """SAP-only customer — never CRM-imported or self-registered."""
        from app.services import customer_profile_service

        mock_txn_repo.get_by_customer_in_store.return_value = [
            make_transaction(customer_name="Somchai Jaidee", created_at=datetime(2026, 1, 5)),
        ]
        mock_cust_repo.get_by_id.return_value = None
        db = MagicMock()

        result = customer_profile_service.get_profile(db, "C2", store_id=1)

        assert result["customer_id"] == "C2"
        assert result["name"] == "Somchai Jaidee"
        assert result["do_not_contact"] is False
        assert result["source"] == "sap_only"

    @patch("app.services.customer_profile_service.customer_repo")
    @patch("app.services.customer_profile_service.transaction_repo")
    def test_fallback_created_at_spans_earliest_and_latest_transaction(self, mock_txn_repo, mock_cust_repo):
        from app.services import customer_profile_service

        mock_txn_repo.get_by_customer_in_store.return_value = [
            make_transaction(created_at=datetime(2026, 3, 1)),
            make_transaction(created_at=datetime(2026, 1, 1)),
        ]
        mock_cust_repo.get_by_id.return_value = None
        db = MagicMock()

        result = customer_profile_service.get_profile(db, "C2", store_id=1)

        assert result["created_at"] == str(datetime(2026, 1, 1))
        assert result["updated_at"] == str(datetime(2026, 3, 1))
