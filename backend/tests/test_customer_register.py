"""
TDD — customer_register_service.py (QA-3) + router.
Manual point-of-sale registration. customer_id optional (assigns
TMP-prefixed temp id when omitted). Providing an existing customer_id
is rejected (409) — this is register, not upsert.
"""
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.services.auth_service import AuthService
from app.services.customer_register_service import (
    CustomerRegisterService,
    CustomerAlreadyExistsError,
)


def make_token(staff_id=90001, role="store_manager", store_id=8902) -> str:
    return AuthService.create_access_token({"staff_id": staff_id, "role": role, "store_id": store_id})


class TestCustomerRegisterServiceUnit:
    def test_valid_registration_with_explicit_customer_id(self):
        db = MagicMock()
        with patch("app.services.customer_register_service.customer_repo") as mock_repo:
            mock_repo.get_by_id.return_value = None
            service = CustomerRegisterService()
            service.register(db, name="สมชาย ใจดี", phone="0811111111", email=None, customer_id="C99", staff_id=90001)

        mock_repo.register.assert_called_once()
        call_data = mock_repo.register.call_args[0][1]
        assert call_data["customer_id"] == "C99"
        assert call_data["language"] == "th"
        assert call_data["staff_id"] == 90001

    def test_registration_without_customer_id_assigns_temp_id(self):
        db = MagicMock()
        with patch("app.services.customer_register_service.customer_repo") as mock_repo:
            mock_repo.assign_temp_id.return_value = "TMP-abc123"
            service = CustomerRegisterService()
            service.register(db, name="John Smith", phone="0822222222", email=None, customer_id=None, staff_id=90001)

        mock_repo.assign_temp_id.assert_called_once()
        call_data = mock_repo.register.call_args[0][1]
        assert call_data["customer_id"] == "TMP-abc123"

    def test_duplicate_customer_id_raises(self):
        db = MagicMock()
        existing = MagicMock()
        with patch("app.services.customer_register_service.customer_repo") as mock_repo:
            mock_repo.get_by_id.return_value = existing
            service = CustomerRegisterService()
            with pytest.raises(CustomerAlreadyExistsError):
                service.register(db, name="Test", phone="0833333333", email=None, customer_id="C1", staff_id=90001)

    def test_language_detected_for_five_name_types(self):
        db = MagicMock()
        cases = [
            ("สมชาย ใจดี", "th"),
            ("John Smith", "en"),
            ("JOHN SMITH", "en"),
            ("", "en"),
            ("สมชาย Mr.", "th"),
        ]
        for name, expected_lang in cases:
            with patch("app.services.customer_register_service.customer_repo") as mock_repo:
                mock_repo.get_by_id.return_value = None
                mock_repo.assign_temp_id.return_value = "TMP-x"
                service = CustomerRegisterService()
                service.register(db, name=name, phone="0810000000", email=None, customer_id=None, staff_id=90001)
                assert mock_repo.register.call_args[0][1]["language"] == expected_lang


class TestCustomerRegisterRouter:
    def test_valid_registration_returns_201(self):
        token = make_token()
        fake_customer = MagicMock()
        fake_customer.customer_id = "TMP-abc"
        fake_customer.name = "John Smith"
        fake_customer.phone = "0811111111"
        fake_customer.email = None
        fake_customer.line_id = None
        fake_customer.language = "en"
        fake_customer.language_source = "auto_detected"
        fake_customer.do_not_contact = False
        fake_customer.source = "manual_registration"
        fake_customer.created_at = "2026-07-21T00:00:00"
        fake_customer.updated_at = "2026-07-21T00:00:00"
        with patch("app.routers.customers.CustomerRegisterService") as MockService:
            MockService.return_value.register.return_value = fake_customer
            client = TestClient(app)
            resp = client.post(
                "/api/v1/customers/register",
                json={"name": "John Smith", "phone": "0811111111"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 201

    def test_missing_phone_returns_422(self):
        token = make_token()
        client = TestClient(app)
        resp = client.post(
            "/api/v1/customers/register",
            json={"name": "John Smith"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    def test_duplicate_customer_id_returns_409(self):
        token = make_token()
        with patch("app.routers.customers.CustomerRegisterService") as MockService:
            MockService.return_value.register.side_effect = CustomerAlreadyExistsError("C1 exists")
            client = TestClient(app)
            resp = client.post(
                "/api/v1/customers/register",
                json={"name": "John Smith", "phone": "0811111111", "customer_id": "C1"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 409

    def test_without_jwt_returns_403(self):
        client = TestClient(app)
        resp = client.post(
            "/api/v1/customers/register",
            json={"name": "John Smith", "phone": "0811111111"},
        )
        assert resp.status_code in (401, 403)
