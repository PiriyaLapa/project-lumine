"""
TDD — Customer Profile endpoints.
GET /api/v1/customers/{customer_id}
GET /api/v1/customers/{customer_id}/transactions
GET /api/v1/customers/{customer_id}/tasks

Store-wide within a store — deliberate exception to the general "own data
only" Auth Rule, documented in CLAUDE.md. Never exposes phone/email/line_id.
Written before implementation — red until the router is updated.
"""
from datetime import date, datetime
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.auth_service import AuthService
from app.models.follow_up_task import FollowUpTask
from app.models.transaction import Transaction


def bearer(role="sales_associate", staff_id=1, store_id=8901):
    token = AuthService.create_access_token(
        {"staff_id": staff_id, "role": role, "store_id": store_id}
    )
    return {"Authorization": f"Bearer {token}"}


def make_task_row(task_id=1, status="Pending"):
    t = MagicMock(spec=FollowUpTask)
    t.id = task_id
    t.customer_id = "CUST001"
    t.task_type = "2D"
    t.task_basis = "posting_date"
    t.due_date = date(2026, 5, 1)
    t.calculated_from = date(2026, 4, 29)
    t.status = status
    t.created_at = "2026-04-29T00:00:00"
    t.updated_at = "2026-04-29T00:00:00"
    return (t, "Benz", "Somchai Jaidee")


def make_transaction(idoc="IDOC001", price=1500, returned=False):
    t = MagicMock(spec=Transaction)
    t.idoc_number = idoc
    t.posting_date = date(2026, 4, 29)
    t.material_desc = "Leather Wallet"
    t.price = price
    t.returned = returned
    t.sales_rep_name = "Benz"
    return t


class TestCustomerProfileEndpoint:
    def test_requires_jwt(self):
        client = TestClient(app)
        resp = client.get("/api/v1/customers/CUST001")
        assert resp.status_code == 403

    @patch("app.routers.customers.customer_profile_service")
    def test_returns_profile_scoped_to_requester_store(self, mock_service):
        mock_service.get_profile.return_value = {
            "customer_id": "CUST001",
            "name": "Somchai Jaidee",
            "do_not_contact": False,
            "source": "crm_import",
            "created_at": "2026-01-01 00:00:00",
            "updated_at": "2026-01-01 00:00:00",
        }
        client = TestClient(app)
        resp = client.get("/api/v1/customers/CUST001", headers=bearer(store_id=8901))

        assert resp.status_code == 200
        body = resp.json()
        assert body["customer_id"] == "CUST001"
        assert body["name"] == "Somchai Jaidee"
        assert "phone" not in body
        assert "email" not in body
        assert "line_id" not in body
        mock_service.get_profile.assert_called_once()
        assert mock_service.get_profile.call_args[0][2] == 8901  # store_id passed through

    @patch("app.routers.customers.customer_profile_service")
    def test_404_when_no_transactions_in_requester_store(self, mock_service):
        """Also covers cross-store customers — avoids leaking existence."""
        mock_service.get_profile.return_value = None
        client = TestClient(app)
        resp = client.get("/api/v1/customers/CUST_OTHER_STORE", headers=bearer(store_id=8901))
        assert resp.status_code == 404


class TestCustomerTransactionsEndpoint:
    def test_requires_jwt(self):
        client = TestClient(app)
        resp = client.get("/api/v1/customers/CUST001/transactions")
        assert resp.status_code == 403

    @patch("app.routers.customers.transaction_repo")
    def test_returns_transactions_scoped_to_requester_store(self, mock_repo):
        mock_repo.get_by_customer_in_store.return_value = [make_transaction()]
        client = TestClient(app)
        resp = client.get(
            "/api/v1/customers/CUST001/transactions", headers=bearer(store_id=8901)
        )

        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 1
        assert body[0]["idoc_number"] == "IDOC001"
        assert body[0]["material_desc"] == "Leather Wallet"
        assert body[0]["price"] == 1500
        assert body[0]["staff_name"] == "Benz"
        mock_repo.get_by_customer_in_store.assert_called_once_with(
            mock_repo.get_by_customer_in_store.call_args[0][0], "CUST001", 8901
        )

    @patch("app.routers.customers.transaction_repo")
    def test_empty_list_when_no_transactions_in_store(self, mock_repo):
        mock_repo.get_by_customer_in_store.return_value = []
        client = TestClient(app)
        resp = client.get(
            "/api/v1/customers/CUST001/transactions", headers=bearer(store_id=8901)
        )
        assert resp.status_code == 200
        assert resp.json() == []


class TestCustomerTasksEndpoint:
    def test_requires_jwt(self):
        client = TestClient(app)
        resp = client.get("/api/v1/customers/CUST001/tasks")
        assert resp.status_code == 403

    @patch("app.routers.customers.task_repo")
    def test_returns_all_status_tasks_scoped_to_requester_store(self, mock_repo):
        mock_repo.get_all_by_customer_in_store.return_value = [
            make_task_row(task_id=1, status="Superseded"),
            make_task_row(task_id=2, status="Done"),
            make_task_row(task_id=3, status="Pending"),
        ]
        client = TestClient(app)
        resp = client.get("/api/v1/customers/CUST001/tasks", headers=bearer(store_id=8901))

        assert resp.status_code == 200
        body = resp.json()
        assert len(body) == 3
        statuses = {t["status"] for t in body}
        assert statuses == {"Superseded", "Done", "Pending"}
        call_args = mock_repo.get_all_by_customer_in_store.call_args
        assert call_args[0][1] == "CUST001"
        assert call_args[0][2] == 8901
