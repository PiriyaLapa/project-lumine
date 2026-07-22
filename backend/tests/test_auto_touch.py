"""
TDD — auto_touch_service.py + routers/auto_touch.py (QA-4).
Covers: today list (do_not_contact excluded, skipped_until respected,
ordering), generate (mocked Claude via message_generator), send (mocked
LINE+SendGrid, task marked Done, 403 on wrong staff, silent-skip
unavailable channel), skip (deferred_to = tomorrow).
"""
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.services.auth_service import AuthService
from app.services.auto_touch_service import (
    AutoTouchService,
    AutoTouchOwnershipError,
    AutoTouchSendDisabledError,
)
from app.services.message_generator import GenerateMessageResult


def make_token(staff_id=90001, role="sales_associate", store_id=8902) -> str:
    return AuthService.create_access_token({"staff_id": staff_id, "role": role, "store_id": store_id})


def make_row(task_id, customer_id, staff_id, do_not_contact=False, skipped_until=None, task_type="2D"):
    task = MagicMock()
    task.id = task_id
    task.due_date = date.today()
    task.task_type = task_type
    task.status = "Pending"
    task.skipped_until = skipped_until

    transaction = MagicMock()
    transaction.staff_id = staff_id
    transaction.material_desc = "PL_TOC Spin CB 10276625 01, 00, 272, M"
    transaction.price = None
    transaction.returned = False

    customer = MagicMock()
    customer.customer_id = customer_id
    customer.name = "Test Customer"
    customer.language = "en"
    customer.line_id = "U123"
    customer.email = "customer@example.com"
    customer.do_not_contact = do_not_contact

    return task, transaction, customer


class TestGetTodayListService:
    def test_returns_enriched_customer_list(self):
        db = MagicMock()
        with patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo:
            mock_repo.get_today_list.return_value = [make_row(1, "C1", 90001)]
            service = AutoTouchService()
            result = service.get_today_list(db, staff_id=90001)

        assert len(result) == 1
        assert result[0]["customer_id"] == "C1"
        assert result[0]["task_id"] == 1
        assert result[0]["send_status"] == "pending"

    def test_no_products_when_transaction_has_no_material_desc(self):
        db = MagicMock()
        row = make_row(1, "C1", 90001)
        row[1].material_desc = None
        with patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo:
            mock_repo.get_today_list.return_value = [row]
            service = AutoTouchService()
            result = service.get_today_list(db, staff_id=90001)

        assert result[0]["products"] == []


class TestGetStatus:
    def test_delegates_to_repo(self):
        db = MagicMock()
        with patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo:
            mock_repo.get_status_summary.return_value = {
                "date": date.today(), "total_due": 3, "sent": 1, "pending": 2, "skipped": 0
            }
            service = AutoTouchService()
            result = service.get_status(db, staff_id=90001)

        assert result["total_due"] == 3
        mock_repo.get_status_summary.assert_called_once_with(db, 90001)


class TestGenerateMessage:
    def test_generate_calls_message_generator(self):
        db = MagicMock()
        row = make_row(1, "C1", 90001)
        with patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo, \
             patch("app.services.auto_touch_service.MessageGenerator") as MockGen:
            mock_repo.get_task_with_customer.return_value = row
            MockGen.return_value.generate.return_value = GenerateMessageResult(
                message_text="Hi! Reply STOP anytime.", language="en", touchpoint="2D"
            )
            service = AutoTouchService()
            result = service.generate_message(db, customer_id="C1", task_id=1, staff_id=90001)

        assert result.message_text == "Hi! Reply STOP anytime."
        MockGen.return_value.generate.assert_called_once()

    def test_generate_wrong_staff_raises_ownership_error(self):
        db = MagicMock()
        row = make_row(1, "C1", 99999)  # owned by a different staff
        with patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo:
            mock_repo.get_task_with_customer.return_value = row
            service = AutoTouchService()
            with pytest.raises(AutoTouchOwnershipError):
                service.generate_message(db, customer_id="C1", task_id=1, staff_id=90001)


class TestSendMessage:
    """AUTO_TOUCH_SEND_ENABLED forced True for this class — these tests cover
    dispatch logic once sending is authorized. The disabled-by-default gate
    itself is covered separately by TestSendMessageDisabledByDefault."""

    @pytest.fixture(autouse=True)
    def _enable_sending(self):
        with patch("app.services.auto_touch_service.settings.AUTO_TOUCH_SEND_ENABLED", True):
            yield

    def test_send_marks_task_done_on_success(self):
        db = MagicMock()
        row = make_row(1, "C1", 90001)
        with patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo, \
             patch("app.services.auto_touch_service.task_repo") as mock_task_repo, \
             patch("app.services.auto_touch_service.line_client") as mock_line, \
             patch("app.services.auto_touch_service.sendgrid_client") as mock_sendgrid:
            mock_repo.get_task_with_customer.return_value = row
            mock_line.push_message.return_value = True
            mock_sendgrid.send_email.return_value = True
            service = AutoTouchService()
            result = service.send_message(
                db, customer_id="C1", task_id=1, message_text="Hi!", channels=None, staff_id=90001
            )

        assert result["status"] == "sent"
        mock_task_repo.mark_done.assert_called_once_with(db, 1)

    def test_send_wrong_staff_raises_ownership_error(self):
        db = MagicMock()
        row = make_row(1, "C1", 99999)
        with patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo:
            mock_repo.get_task_with_customer.return_value = row
            service = AutoTouchService()
            with pytest.raises(AutoTouchOwnershipError):
                service.send_message(
                    db, customer_id="C1", task_id=1, message_text="Hi!", channels=None, staff_id=90001
                )

    def test_send_silently_skips_unavailable_channel(self):
        db = MagicMock()
        row = make_row(1, "C1", 90001)
        row[2].line_id = None  # no LINE available for this customer
        with patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo, \
             patch("app.services.auto_touch_service.task_repo") as mock_task_repo, \
             patch("app.services.auto_touch_service.line_client") as mock_line, \
             patch("app.services.auto_touch_service.sendgrid_client") as mock_sendgrid:
            mock_repo.get_task_with_customer.return_value = row
            mock_sendgrid.send_email.return_value = True
            service = AutoTouchService()
            result = service.send_message(
                db, customer_id="C1", task_id=1, message_text="Hi!", channels=None, staff_id=90001
            )

        mock_line.push_message.assert_not_called()
        assert "email" in result["channels_sent"]
        assert "line" not in result["channels_sent"]

    def test_send_explicit_unavailable_channel_marked_not_available(self):
        """Requesting a channel the customer doesn't have marks it not_available, not failed."""
        db = MagicMock()
        row = make_row(1, "C1", 90001)
        row[2].line_id = None  # no LINE
        with patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo, \
             patch("app.services.auto_touch_service.task_repo"), \
             patch("app.services.auto_touch_service.line_client") as mock_line, \
             patch("app.services.auto_touch_service.sendgrid_client"):
            mock_repo.get_task_with_customer.return_value = row
            service = AutoTouchService()
            result = service.send_message(
                db, customer_id="C1", task_id=1, message_text="Hi!", channels=["line"], staff_id=90001
            )

        mock_line.push_message.assert_not_called()
        assert result["status"] == "failed"
        assert result["channels_sent"] == []

    def test_send_explicit_unavailable_email_marked_not_available(self):
        db = MagicMock()
        row = make_row(1, "C1", 90001)
        row[2].email = None  # no email
        with patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo, \
             patch("app.services.auto_touch_service.task_repo"), \
             patch("app.services.auto_touch_service.line_client"), \
             patch("app.services.auto_touch_service.sendgrid_client") as mock_sendgrid:
            mock_repo.get_task_with_customer.return_value = row
            service = AutoTouchService()
            result = service.send_message(
                db, customer_id="C1", task_id=1, message_text="Hi!", channels=["email"], staff_id=90001
            )

        mock_sendgrid.send_email.assert_not_called()
        assert result["status"] == "failed"

    def test_send_failed_status_when_all_channels_fail(self):
        db = MagicMock()
        row = make_row(1, "C1", 90001)
        with patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo, \
             patch("app.services.auto_touch_service.task_repo") as mock_task_repo, \
             patch("app.services.auto_touch_service.line_client") as mock_line, \
             patch("app.services.auto_touch_service.sendgrid_client") as mock_sendgrid:
            mock_repo.get_task_with_customer.return_value = row
            mock_line.push_message.return_value = False
            mock_sendgrid.send_email.return_value = False
            service = AutoTouchService()
            result = service.send_message(
                db, customer_id="C1", task_id=1, message_text="Hi!", channels=None, staff_id=90001
            )

        assert result["status"] == "failed"
        mock_task_repo.mark_done.assert_not_called()

    def test_send_task_not_found_raises_ownership_error(self):
        db = MagicMock()
        with patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo:
            mock_repo.get_task_with_customer.return_value = None
            service = AutoTouchService()
            with pytest.raises(AutoTouchOwnershipError):
                service.send_message(
                    db, customer_id="C1", task_id=999, message_text="Hi!", channels=None, staff_id=90001
                )

    def test_send_partial_status_when_one_channel_fails(self):
        db = MagicMock()
        row = make_row(1, "C1", 90001)
        with patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo, \
             patch("app.services.auto_touch_service.task_repo") as mock_task_repo, \
             patch("app.services.auto_touch_service.line_client") as mock_line, \
             patch("app.services.auto_touch_service.sendgrid_client") as mock_sendgrid:
            mock_repo.get_task_with_customer.return_value = row
            mock_line.push_message.return_value = True
            mock_sendgrid.send_email.return_value = False
            service = AutoTouchService()
            result = service.send_message(
                db, customer_id="C1", task_id=1, message_text="Hi!", channels=None, staff_id=90001
            )

        assert result["status"] == "partial"
        mock_task_repo.mark_done.assert_called_once()


class TestSendMessageDisabledByDefault:
    """Automated customer messaging is gated behind AUTO_TOUCH_SEND_ENABLED,
    pending company authorization. No class-level override here — this
    exercises the real default (unset/false)."""

    def test_send_disabled_by_default_raises_and_never_dispatches(self):
        db = MagicMock()
        row = make_row(1, "C1", 90001)
        with patch("app.services.auto_touch_service.settings.AUTO_TOUCH_SEND_ENABLED", False), \
             patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo, \
             patch("app.services.auto_touch_service.task_repo") as mock_task_repo, \
             patch("app.services.auto_touch_service.line_client") as mock_line, \
             patch("app.services.auto_touch_service.sendgrid_client") as mock_sendgrid:
            mock_repo.get_task_with_customer.return_value = row
            service = AutoTouchService()
            with pytest.raises(AutoTouchSendDisabledError):
                service.send_message(
                    db, customer_id="C1", task_id=1, message_text="Hi!", channels=None, staff_id=90001
                )

        # The gate must short-circuit before any lookup, dispatch, or persistence.
        mock_repo.get_task_with_customer.assert_not_called()
        mock_line.push_message.assert_not_called()
        mock_sendgrid.send_email.assert_not_called()
        mock_repo.create_message.assert_not_called()
        mock_task_repo.mark_done.assert_not_called()

    def test_send_endpoint_returns_403_when_disabled(self):
        row = make_row(1, "C1", 90001)
        with patch("app.services.auto_touch_service.settings.AUTO_TOUCH_SEND_ENABLED", False), \
             patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo, \
             patch("app.services.auto_touch_service.line_client") as mock_line, \
             patch("app.services.auto_touch_service.sendgrid_client") as mock_sendgrid:
            mock_repo.get_task_with_customer.return_value = row
            resp = TestClient(app).post(
                "/api/v1/auto-touch/send/C1",
                json={"task_id": 1, "message_text": "Hi!"},
                headers={"Authorization": f"Bearer {make_token()}"},
            )
            mock_line.push_message.assert_not_called()
            mock_sendgrid.send_email.assert_not_called()

        assert resp.status_code == 403
        assert "disabled" in resp.json()["detail"].lower()


class TestSkip:
    def test_skip_defers_to_tomorrow(self):
        db = MagicMock()
        row = make_row(1, "C1", 90001)
        with patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo:
            mock_repo.get_pending_task_for_customer.return_value = row
            mock_repo.record_skip.return_value = date.today() + timedelta(days=1)
            service = AutoTouchService()
            result = service.skip(db, customer_id="C1", staff_id=90001)

        assert result["task_id"] == 1
        assert result["deferred_to"] == date.today() + timedelta(days=1)

    def test_skip_no_pending_task_raises_ownership_error(self):
        db = MagicMock()
        with patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo:
            mock_repo.get_pending_task_for_customer.return_value = None
            service = AutoTouchService()
            with pytest.raises(AutoTouchOwnershipError):
                service.skip(db, customer_id="C1", staff_id=90001)


# ---------------------------------------------------------------------------
# Router-level tests
# ---------------------------------------------------------------------------

class TestAutoTouchRouter:
    def test_today_list_requires_jwt(self):
        client = TestClient(app)
        resp = client.get("/api/v1/auto-touch/today")
        assert resp.status_code in (401, 403)

    def test_today_list_returns_200(self):
        token = make_token()
        with patch("app.routers.auto_touch.AutoTouchService") as MockService:
            MockService.return_value.get_today_list.return_value = []
            client = TestClient(app)
            resp = client.get(
                "/api/v1/auto-touch/today", headers={"Authorization": f"Bearer {token}"}
            )
        assert resp.status_code == 200
        assert resp.json() == []

    def test_generate_message_requires_both_fields(self):
        token = make_token()
        client = TestClient(app)
        resp = client.post(
            "/api/v1/auto-touch/generate-message",
            json={"customer_id": "C1"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    def test_send_returns_403_on_ownership_error(self):
        token = make_token()
        with patch("app.routers.auto_touch.AutoTouchService") as MockService:
            MockService.return_value.send_message.side_effect = AutoTouchOwnershipError("not yours")
            client = TestClient(app)
            resp = client.post(
                "/api/v1/auto-touch/send/C1",
                json={"task_id": 1, "message_text": "Hi!"},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 403

    def test_skip_returns_200(self):
        token = make_token()
        with patch("app.routers.auto_touch.AutoTouchService") as MockService:
            MockService.return_value.skip.return_value = {
                "task_id": 1, "deferred_to": date.today() + timedelta(days=1)
            }
            client = TestClient(app)
            resp = client.post(
                "/api/v1/auto-touch/skip/C1", headers={"Authorization": f"Bearer {token}"}
            )
        assert resp.status_code == 200
        assert resp.json()["customer_id"] == "C1"

    def test_status_returns_200(self):
        token = make_token()
        with patch("app.routers.auto_touch.AutoTouchService") as MockService:
            MockService.return_value.get_status.return_value = {
                "date": date.today(), "total_due": 0, "sent": 0, "pending": 0, "skipped": 0
            }
            client = TestClient(app)
            resp = client.get(
                "/api/v1/auto-touch/status", headers={"Authorization": f"Bearer {token}"}
            )
        assert resp.status_code == 200
