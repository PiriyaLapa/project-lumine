"""
TDD — crm_import_service.py (QA-2).
CRM Excel export: Customer ID, Customer Name, Phone, Email — fixed
columns (not SAP, so no JSON column-map per architect decision).
On name conflict: do not update ANY field for that row, only flag it —
avoids partial-write ambiguity.
"""
from io import BytesIO
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.auth_service import AuthService
from app.services.crm_import_service import CRMImportService, CRMImportError, CRMImportResult


def make_excel(rows: list[dict]) -> BytesIO:
    df = pd.DataFrame(rows)
    buf = BytesIO()
    df.to_excel(buf, index=False)
    buf.seek(0)
    return buf


class TestCRMImportValid:
    def test_new_customer_created(self):
        file = make_excel([
            {"Customer ID": "C1", "Customer Name": "สมชาย ใจดี", "Phone": "0811111111", "Email": ""},
        ])
        db = MagicMock()
        with patch("app.services.crm_import_service.customer_repo") as mock_repo:
            mock_repo.get_by_id.return_value = None
            service = CRMImportService(staff_id=90001)
            result = service.import_file(db, file, "export.xlsx")

        assert result.created == 1
        assert result.updated == 0
        assert result.conflicts == 0
        mock_repo.create.assert_called_once()
        created_data = mock_repo.create.call_args[0][1]
        assert created_data["language"] == "th"
        assert created_data["staff_id"] == 90001

    def test_existing_customer_matching_name_updated(self):
        file = make_excel([
            {"Customer ID": "C1", "Customer Name": "John Smith", "Phone": "0822222222", "Email": "j@x.com"},
        ])
        db = MagicMock()
        existing = MagicMock()
        existing.customer_id = "C1"
        existing.name = "John Smith"
        with patch("app.services.crm_import_service.customer_repo") as mock_repo:
            mock_repo.get_by_id.return_value = existing
            service = CRMImportService(staff_id=90001)
            result = service.import_file(db, file, "export.xlsx")

        assert result.updated == 1
        assert result.created == 0
        assert result.conflicts == 0
        mock_repo.update_contact_info.assert_called_once()

    def test_name_conflict_flagged_not_applied(self):
        file = make_excel([
            {"Customer ID": "C1", "Customer Name": "Different Name", "Phone": "0833333333", "Email": ""},
        ])
        db = MagicMock()
        existing = MagicMock()
        existing.customer_id = "C1"
        existing.name = "Original Name"
        with patch("app.services.crm_import_service.customer_repo") as mock_repo:
            mock_repo.get_by_id.return_value = existing
            service = CRMImportService(staff_id=90001)
            result = service.import_file(db, file, "export.xlsx")

        assert result.conflicts == 1
        assert result.updated == 0
        assert result.created == 0
        assert result.conflict_details[0] == {
            "customer_id": "C1",
            "existing_name": "Original Name",
            "import_name": "Different Name",
        }
        mock_repo.update_contact_info.assert_not_called()
        mock_repo.create.assert_not_called()

    def test_mixed_new_and_existing_rows(self):
        file = make_excel([
            {"Customer ID": "C1", "Customer Name": "Existing", "Phone": "0811111111", "Email": ""},
            {"Customer ID": "C2", "Customer Name": "New One", "Phone": "0822222222", "Email": ""},
        ])
        db = MagicMock()
        existing = MagicMock()
        existing.customer_id = "C1"
        existing.name = "Existing"

        with patch("app.services.crm_import_service.customer_repo") as mock_repo:
            mock_repo.get_by_id.side_effect = lambda db, cid: existing if cid == "C1" else None
            service = CRMImportService(staff_id=90001)
            result = service.import_file(db, file, "export.xlsx")

        assert result.updated == 1
        assert result.created == 1
        assert result.conflicts == 0


class TestCRMImportInvalid:
    def test_missing_required_column_raises(self):
        file = make_excel([{"Customer ID": "C1", "Phone": "0811111111"}])  # no Customer Name
        db = MagicMock()
        service = CRMImportService(staff_id=90001)
        with pytest.raises(CRMImportError):
            service.import_file(db, file, "export.xlsx")

    def test_empty_file_raises(self):
        file = make_excel([])
        db = MagicMock()
        service = CRMImportService(staff_id=90001)
        with pytest.raises(CRMImportError):
            service.import_file(db, file, "export.xlsx")

    def test_unreadable_file_raises(self):
        file = BytesIO(b"this is not a valid excel file at all")
        db = MagicMock()
        service = CRMImportService(staff_id=90001)
        with pytest.raises(CRMImportError):
            service.import_file(db, file, "corrupt.xlsx")


class TestCRMImportPII:
    def test_no_pii_in_log_calls(self):
        """Phone/email must never appear in any logger call."""
        file = make_excel([
            {"Customer ID": "C1", "Customer Name": "John Smith", "Phone": "0899999999", "Email": "secret@x.com"},
        ])
        db = MagicMock()
        with patch("app.services.crm_import_service.customer_repo") as mock_repo, \
             patch("app.services.crm_import_service.logger") as mock_logger:
            mock_repo.get_by_id.return_value = None
            service = CRMImportService(staff_id=90001)
            service.import_file(db, file, "export.xlsx")

        all_log_text = " ".join(
            str(call) for call in (mock_logger.info.call_args_list + mock_logger.warning.call_args_list)
        )
        assert "0899999999" not in all_log_text
        assert "secret@x.com" not in all_log_text


def make_token(staff_id=90001, role="store_manager", store_id=8902) -> str:
    return AuthService.create_access_token({"staff_id": staff_id, "role": role, "store_id": store_id})


class TestCRMImportRouter:
    def test_valid_upload_returns_200(self):
        token = make_token()
        file = make_excel([{"Customer ID": "C1", "Customer Name": "New", "Phone": "0811111111", "Email": ""}])
        with patch("app.routers.customers.CRMImportService") as MockService:
            MockService.return_value.import_file.return_value = CRMImportResult(created=1)
            client = TestClient(app)
            resp = client.post(
                "/api/v1/customers/import-crm",
                files={"file": ("export.xlsx", file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 200
        assert resp.json()["created"] == 1

    def test_malformed_file_returns_400(self):
        token = make_token()
        with patch("app.routers.customers.CRMImportService") as MockService:
            MockService.return_value.import_file.side_effect = CRMImportError("bad file")
            client = TestClient(app)
            resp = client.post(
                "/api/v1/customers/import-crm",
                files={"file": ("bad.xlsx", BytesIO(b"not an excel file"), "application/octet-stream")},
                headers={"Authorization": f"Bearer {token}"},
            )
        assert resp.status_code == 400

    def test_without_jwt_returns_403(self):
        client = TestClient(app)
        resp = client.post(
            "/api/v1/customers/import-crm",
            files={"file": ("export.xlsx", BytesIO(b"x"), "application/octet-stream")},
        )
        assert resp.status_code in (401, 403)
