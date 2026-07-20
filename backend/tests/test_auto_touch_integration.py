"""
QA-6 — full Auto-Touch end-to-end integration test.

Unlike test_auto_touch.py / test_crm_import.py / test_customer_register.py
(which patch entire service classes at the router boundary), this file
patches only at the repository / external-client boundary — customer_repo,
auto_touch_repo, task_repo, line_client, sendgrid_client, and the Anthropic
SDK client. That lets the real CRMImportService, CustomerRegisterService,
and AutoTouchService logic run for real, chained together through actual
HTTP calls via TestClient, proving the router -> service -> repository
wiring actually works end to end.
"""
import logging
from datetime import date, timedelta
from io import BytesIO
from unittest.mock import ANY, MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.services.auth_service import AuthService
from app.services.message_generator import PDPA_OPT_OUT_EN


def make_token(staff_id=90001, role="sales_associate", store_id=8902) -> str:
    return AuthService.create_access_token({"staff_id": staff_id, "role": role, "store_id": store_id})


def bearer(staff_id=90001, role="sales_associate", store_id=8902) -> dict:
    return {"Authorization": f"Bearer {make_token(staff_id, role, store_id)}"}


def override_get_db():
    yield MagicMock()


@pytest.fixture(autouse=True)
def _override_db():
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


def make_excel(rows: list[dict]) -> BytesIO:
    df = pd.DataFrame(rows)
    buf = BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)
    return buf


def make_anthropic_response(text: str):
    resp = MagicMock()
    block = MagicMock()
    block.type = "text"
    block.text = text
    resp.content = [block]
    return resp


def make_row(
    task_id, customer_id, staff_id, do_not_contact=False, skipped_until=None,
    task_type="2D", line_id="U123", email="customer@example.com", name="Test Customer",
):
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
    customer.name = name
    customer.language = "en"
    customer.line_id = line_id
    customer.email = email
    customer.do_not_contact = do_not_contact

    return task, transaction, customer


def make_fake_registered_customer(customer_id, name, phone, email=None, line_id=None, language="en"):
    fake = MagicMock()
    fake.customer_id = customer_id
    fake.name = name
    fake.phone = phone
    fake.email = email
    fake.line_id = line_id
    fake.language = language
    fake.language_source = "auto_detected"
    fake.do_not_contact = False
    fake.source = "manual_registration"
    fake.created_at = "2026-07-21T00:00:00"
    fake.updated_at = "2026-07-21T00:00:00"
    return fake


class TestFullHappyPathChain:
    def test_crm_import_then_register_then_today_list_then_generate_then_send_then_status(self):
        client = TestClient(app)

        # 1. CRM import
        with patch("app.services.crm_import_service.customer_repo") as mock_customer_repo:
            mock_customer_repo.get_by_id.return_value = None
            file = make_excel(
                [{"Customer ID": "C-CRM1", "Customer Name": "John Import", "Phone": "0811111111", "Email": ""}]
            )
            resp = client.post(
                "/api/v1/customers/import-crm",
                files={
                    "file": (
                        "export.xlsx",
                        file,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
                headers=bearer(),
            )
        assert resp.status_code == 200
        assert resp.json()["created"] == 1
        assert resp.json()["conflicts"] == 0

        # 2. Register a new customer
        fake_customer = make_fake_registered_customer(
            "TMP-e2e0001", "Jane Register", "0822222222", line_id="Ue2eline001"
        )
        with patch("app.services.customer_register_service.customer_repo") as mock_customer_repo:
            mock_customer_repo.assign_temp_id.return_value = "TMP-e2e0001"
            mock_customer_repo.register.return_value = fake_customer
            resp = client.post(
                "/api/v1/customers/register",
                json={"name": "Jane Register", "phone": "0822222222"},
                headers=bearer(),
            )
        assert resp.status_code == 201
        customer_id = resp.json()["customer_id"]
        assert customer_id == "TMP-e2e0001"

        # 3. Today list shows the registered customer's due task
        with patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo:
            mock_repo.get_today_list.return_value = [make_row(501, customer_id, 90001)]
            resp = client.get("/api/v1/auto-touch/today", headers=bearer())
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["customer_id"] == customer_id
        assert data[0]["task_id"] == 501
        assert data[0]["send_status"] == "pending"
        assert data[0]["channels_available"] == {"email": True, "line": True}

        # 4. Generate a draft message (Anthropic mocked, PDPA line enforced)
        with patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo, \
             patch("app.services.message_generator.anthropic.Anthropic") as MockClient:
            mock_repo.get_task_with_customer.return_value = make_row(501, customer_id, 90001)
            MockClient.return_value.messages.create.return_value = make_anthropic_response(
                f"Hi! Thanks for your purchase. {PDPA_OPT_OUT_EN}"
            )
            resp = client.post(
                "/api/v1/auto-touch/generate-message",
                json={"customer_id": customer_id, "task_id": 501},
                headers=bearer(),
            )
        assert resp.status_code == 200
        message_text = resp.json()["message_text"]
        assert PDPA_OPT_OUT_EN in message_text
        assert resp.json()["touchpoint"] == "2D"

        # 5. Send via both channels
        with patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo, \
             patch("app.services.auto_touch_service.task_repo") as mock_task_repo, \
             patch("app.services.auto_touch_service.line_client") as mock_line, \
             patch("app.services.auto_touch_service.sendgrid_client") as mock_sendgrid:
            mock_repo.get_task_with_customer.return_value = make_row(501, customer_id, 90001)
            mock_line.push_message.return_value = True
            mock_sendgrid.send_email.return_value = True
            resp = client.post(
                f"/api/v1/auto-touch/send/{customer_id}",
                json={"task_id": 501, "message_text": message_text},
                headers=bearer(),
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "sent"
        assert data["channels_sent"] == ["line", "email"]
        mock_task_repo.mark_done.assert_called_once_with(ANY, 501)

        # 6. Status reflects the send
        with patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo:
            mock_repo.get_status_summary.return_value = {
                "date": date.today(), "total_due": 1, "sent": 1, "pending": 0, "skipped": 0
            }
            resp = client.get("/api/v1/auto-touch/status", headers=bearer())
        assert resp.status_code == 200
        assert resp.json()["sent"] == 1


class TestSkipPathChain:
    def test_today_list_then_skip_then_status_reflects_skipped_task_still_pending(self):
        client = TestClient(app)

        with patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo:
            mock_repo.get_today_list.return_value = [make_row(601, "C-SKIP1", 90001)]
            resp = client.get("/api/v1/auto-touch/today", headers=bearer())
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        tomorrow = date.today() + timedelta(days=1)
        with patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo:
            mock_repo.get_pending_task_for_customer.return_value = make_row(601, "C-SKIP1", 90001)
            mock_repo.record_skip.return_value = tomorrow
            resp = client.post("/api/v1/auto-touch/skip/C-SKIP1", headers=bearer())
        assert resp.status_code == 200
        assert resp.json() == {"customer_id": "C-SKIP1", "task_id": 601, "deferred_to": tomorrow.isoformat()}

        # Skip defers skipped_until only — it never changes task.status, so the
        # task is simultaneously "pending" and "skipped" in the status summary.
        with patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo:
            mock_repo.get_status_summary.return_value = {
                "date": date.today(), "total_due": 1, "sent": 0, "pending": 1, "skipped": 1
            }
            resp = client.get("/api/v1/auto-touch/status", headers=bearer())
        data = resp.json()
        assert data["pending"] == 1
        assert data["skipped"] == 1


class TestOwnershipIsolation:
    """Task/customer owned by staff 90001; staff 90002 attempts each action."""

    def test_staff_b_cannot_generate_message_for_staff_as_task(self):
        row = make_row(701, "C-OWN1", 90001)
        with patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo:
            mock_repo.get_task_with_customer.return_value = row
            resp = TestClient(app).post(
                "/api/v1/auto-touch/generate-message",
                json={"customer_id": "C-OWN1", "task_id": 701},
                headers=bearer(staff_id=90002),
            )
        assert resp.status_code == 404

    def test_staff_b_cannot_send_for_staff_as_task(self):
        row = make_row(702, "C-OWN2", 90001)
        with patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo, \
             patch("app.services.auto_touch_service.line_client") as mock_line, \
             patch("app.services.auto_touch_service.sendgrid_client") as mock_sendgrid:
            mock_repo.get_task_with_customer.return_value = row
            resp = TestClient(app).post(
                "/api/v1/auto-touch/send/C-OWN2",
                json={"task_id": 702, "message_text": "Hi!"},
                headers=bearer(staff_id=90002),
            )
            # Ownership check must short-circuit before any outbound send attempt.
            mock_line.push_message.assert_not_called()
            mock_sendgrid.send_email.assert_not_called()
        assert resp.status_code == 403

    def test_staff_b_cannot_skip_staff_as_task(self):
        # skip's ownership is enforced at the repo layer (query filtered by
        # staff_id), unlike generate/send which check transaction.staff_id
        # in the service after an unfiltered lookup — so staff B's query
        # legitimately returns None here rather than an owned-but-rejected row.
        with patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo:
            mock_repo.get_pending_task_for_customer.return_value = None
            resp = TestClient(app).post(
                "/api/v1/auto-touch/skip/C-OWN3",
                headers=bearer(staff_id=90002),
            )
        assert resp.status_code == 404


class TestDoNotContactExclusion:
    def test_do_not_contact_customer_excluded_from_today_list(self):
        # The actual SQL filter (Customer.do_not_contact.is_(False)) is
        # covered by test_auto_touch_repo.py — this only confirms the
        # router -> service -> response contract doesn't leak such rows.
        with patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo:
            mock_repo.get_today_list.return_value = []
            resp = TestClient(app).get("/api/v1/auto-touch/today", headers=bearer())
        assert resp.status_code == 200
        assert resp.json() == []


class TestPartialSend:
    def test_send_partial_when_only_one_channel_succeeds(self):
        row = make_row(801, "C-PART1", 90001)
        client = TestClient(app)
        with patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo, \
             patch("app.services.auto_touch_service.task_repo") as mock_task_repo, \
             patch("app.services.auto_touch_service.line_client") as mock_line, \
             patch("app.services.auto_touch_service.sendgrid_client") as mock_sendgrid:
            mock_repo.get_task_with_customer.return_value = row
            mock_line.push_message.return_value = True
            mock_sendgrid.send_email.return_value = False
            resp = client.post(
                "/api/v1/auto-touch/send/C-PART1",
                json={"task_id": 801, "message_text": "Hi!"},
                headers=bearer(),
            )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "partial"
        assert data["channels_sent"] == ["line"]
        mock_task_repo.mark_done.assert_called_once()

        with patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo:
            mock_repo.get_status_summary.return_value = {
                "date": date.today(), "total_due": 1, "sent": 1, "pending": 0, "skipped": 0
            }
            resp = client.get("/api/v1/auto-touch/status", headers=bearer())
        assert resp.json()["sent"] == 1


class TestCustomerIdNotCrossChecked:
    def test_send_echoes_caller_customer_id_without_validating_against_task(self):
        # BUG (found during QA-6 planning, 2026-07-21): send_message resolves
        # the task/customer purely from task_id via _get_owned_row — the
        # customer_id path param is never cross-checked against the row it
        # actually resolves. This test documents current behavior; it does
        # NOT assert this is correct. See auto_touch_service.py send_message.
        # Fixing this is tracked as a separate follow-up decision.
        row = make_row(901, "C-REAL", 90001)
        with patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo, \
             patch("app.services.auto_touch_service.task_repo"), \
             patch("app.services.auto_touch_service.line_client") as mock_line, \
             patch("app.services.auto_touch_service.sendgrid_client") as mock_sendgrid:
            mock_repo.get_task_with_customer.return_value = row
            mock_line.push_message.return_value = True
            mock_sendgrid.send_email.return_value = True
            resp = TestClient(app).post(
                "/api/v1/auto-touch/send/C-DIFFERENT",
                json={"task_id": 901, "message_text": "Hi!"},
                headers=bearer(),
            )
        assert resp.status_code == 200
        assert resp.json()["customer_id"] == "C-DIFFERENT"


class TestPIIAcrossFullChain:
    def test_no_customer_pii_in_log_output_across_chain(self, caplog):
        caplog.set_level(logging.INFO)
        phone = "0899999999"
        email = "secret@example.com"
        line_id = "Usecretline123"
        name = "สมชาย ลับสุดยอด"

        client = TestClient(app)

        with patch("app.services.crm_import_service.customer_repo") as mock_customer_repo:
            mock_customer_repo.get_by_id.return_value = None
            file = make_excel(
                [{"Customer ID": "C-PII1", "Customer Name": name, "Phone": phone, "Email": email}]
            )
            client.post(
                "/api/v1/customers/import-crm",
                files={
                    "file": (
                        "export.xlsx",
                        file,
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                },
                headers=bearer(),
            )

        fake_customer = make_fake_registered_customer(
            "C-PII2", name, phone, email=email, line_id=line_id, language="th"
        )
        with patch("app.services.customer_register_service.customer_repo") as mock_customer_repo:
            mock_customer_repo.get_by_id.return_value = None
            mock_customer_repo.register.return_value = fake_customer
            client.post(
                "/api/v1/customers/register",
                json={"name": name, "phone": phone, "email": email, "customer_id": "C-PII2"},
                headers=bearer(),
            )

        row = make_row(1001, "C-PII2", 90001, line_id=line_id, email=email, name=name)
        with patch("app.services.auto_touch_service.auto_touch_repo") as mock_repo, \
             patch("app.services.auto_touch_service.task_repo"), \
             patch("app.services.auto_touch_service.line_client") as mock_line, \
             patch("app.services.auto_touch_service.sendgrid_client") as mock_sendgrid:
            mock_repo.get_task_with_customer.return_value = row
            mock_line.push_message.return_value = True
            mock_sendgrid.send_email.return_value = True
            client.post(
                "/api/v1/auto-touch/send/C-PII2",
                json={"task_id": 1001, "message_text": "Hi!"},
                headers=bearer(),
            )

        assert phone not in caplog.text
        assert email not in caplog.text
        assert line_id not in caplog.text
