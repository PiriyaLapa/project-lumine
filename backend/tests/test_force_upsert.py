"""
TDD — force upsert: ?force=true re-upload backfills sales_rep_name without
duplicating transactions or re-running CycleReset.

Covers:
  transaction_repo.upsert()  — 3 unit tests  (TestTransactionUpsert)
  POST /upload?force=true    — 2 router tests (TestForceUploadUpsert)
"""
from datetime import date
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.models.transaction import Transaction
from app.models.staff import Staff
from app.services.auth_service import AuthService
from app.repositories.transaction_repo import upsert


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_staff(role="sales_associate", staff_id=1, store_id=8901):
    s = Staff()
    s.id = staff_id
    s.name = "Benz"
    s.employee_code = "56546"
    s.role = role
    s.store_id = store_id
    s.email = "benz@lumine.com"
    s.hashed_password = AuthService.hash_password("secret")
    s.deleted_at = None
    return s


def bearer(role="sales_associate", staff_id=1, store_id=8901):
    token = AuthService.create_access_token(
        {"staff_id": staff_id, "role": role, "store_id": store_id}
    )
    return {"Authorization": f"Bearer {token}"}


def mock_db_with_staff(staff):
    def _override():
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = staff
        yield db
    return _override


UPLOAD_FILE = {"file": ("sap.csv", b"header\nrow", "text/csv")}


def _make_parse_result(idoc="IDOC1", sales_rep_name="Benz"):
    pr = MagicMock()
    pr.records = [{
        "idoc_number": idoc,
        "posting_date": date(2026, 5, 5),
        "customer_id": "C001",
        "ean": None,
        "material_desc": None,
        "sales_rep_name": sales_rep_name,
    }]
    pr.errors = []
    return pr


# ---------------------------------------------------------------------------
# Unit tests — transaction_repo.upsert()
# ---------------------------------------------------------------------------

class TestTransactionUpsert:

    def _data(self, idoc="NEWIDOC", sales_rep_name="Benz"):
        return {
            "idoc_number": idoc,
            "posting_date": date(2026, 5, 5),
            "customer_id": "C001",
            "staff_id": 1,
            "ean": None,
            "material_desc": None,
            "sales_rep_name": sales_rep_name,
        }

    def test_creates_when_idoc_not_exists(self):
        """upsert with unknown idoc → INSERT, returns (transaction, True)."""
        db = MagicMock()
        with patch("app.repositories.transaction_repo.get_by_idoc", return_value=None):
            txn, created = upsert(db, self._data())

        assert created is True
        db.add.assert_called_once()
        db.flush.assert_called_once()

    def test_updates_sales_rep_name_when_idoc_exists(self):
        """upsert with existing idoc → sales_rep_name updated, returns (transaction, False)."""
        existing = MagicMock(spec=Transaction)
        existing.sales_rep_name = None
        db = MagicMock()

        with patch("app.repositories.transaction_repo.get_by_idoc", return_value=existing):
            txn, created = upsert(db, self._data(idoc="EXISTINGIDOC", sales_rep_name="Benz"))

        assert created is False
        assert txn.sales_rep_name == "Benz"
        db.add.assert_not_called()
        db.flush.assert_called_once()

    def test_updates_customer_name_when_idoc_exists(self):
        """upsert with existing idoc → customer_name backfilled too (mirrors sales_rep_name)."""
        existing = MagicMock(spec=Transaction)
        existing.sales_rep_name = None
        existing.customer_name = None
        db = MagicMock()

        data = self._data(idoc="EXISTINGIDOC", sales_rep_name="Benz")
        data["customer_name"] = "Pisit Boonchanya"

        with patch("app.repositories.transaction_repo.get_by_idoc", return_value=existing):
            txn, created = upsert(db, data)

        assert created is False
        assert txn.customer_name == "Pisit Boonchanya"
        db.flush.assert_called_once()

    def test_does_not_insert_duplicate_row(self):
        """upsert with existing idoc → db.add never called (no duplicate INSERT)."""
        existing = MagicMock(spec=Transaction)
        existing.sales_rep_name = None
        db = MagicMock()

        with patch("app.repositories.transaction_repo.get_by_idoc", return_value=existing):
            upsert(db, self._data(idoc="DUP"))

        db.add.assert_not_called()


# ---------------------------------------------------------------------------
# Router tests — POST /api/v1/upload?force=true
# ---------------------------------------------------------------------------

class TestForceUploadUpsert:

    def test_force_existing_idoc_does_not_run_cycle_reset(self):
        """force=True + existing idoc → upsert called, CycleReset NOT run, tasks_created=0."""
        staff = make_staff()
        app.dependency_overrides[get_db] = mock_db_with_staff(staff)
        client = TestClient(app)

        with patch("app.routers.upload.staff_repo") as mock_staff_repo, \
             patch("app.routers.upload.SAPParser") as mock_parser, \
             patch("app.routers.upload.transaction_repo") as mock_txn_repo, \
             patch("app.routers.upload.CycleReset") as mock_reset, \
             patch("app.routers.upload.upload_log_repo") as mock_log_repo:

            mock_staff_repo.get_by_id.return_value = staff
            mock_parser.return_value.parse.return_value = _make_parse_result()
            mock_txn_repo.upsert.return_value = (MagicMock(), False)  # existing row
            mock_log_repo.find_overlap.return_value = None

            resp = client.post(
                "/api/v1/upload?force=true",
                files=UPLOAD_FILE,
                headers=bearer(),
            )

        app.dependency_overrides.clear()
        assert resp.status_code == 200
        mock_txn_repo.upsert.assert_called_once()
        mock_reset.run.assert_not_called()
        assert resp.json()["tasks_created"] == 0

    def test_force_new_idoc_runs_cycle_reset(self):
        """force=True + new idoc → upsert called, CycleReset IS run, tasks_created > 0."""
        staff = make_staff()
        app.dependency_overrides[get_db] = mock_db_with_staff(staff)
        client = TestClient(app)

        with patch("app.routers.upload.staff_repo") as mock_staff_repo, \
             patch("app.routers.upload.SAPParser") as mock_parser, \
             patch("app.routers.upload.transaction_repo") as mock_txn_repo, \
             patch("app.routers.upload.CycleReset") as mock_reset, \
             patch("app.routers.upload.upload_log_repo") as mock_log_repo:

            mock_staff_repo.get_by_id.return_value = staff
            mock_parser.return_value.parse.return_value = _make_parse_result()
            mock_txn_repo.upsert.return_value = (MagicMock(), True)  # new row
            mock_reset.run.return_value = MagicMock(tasks_created=3, cycles_reset=1)
            mock_log_repo.find_overlap.return_value = None

            resp = client.post(
                "/api/v1/upload?force=true",
                files=UPLOAD_FILE,
                headers=bearer(),
            )

        app.dependency_overrides.clear()
        assert resp.status_code == 200
        mock_txn_repo.upsert.assert_called_once()
        mock_reset.run.assert_called_once()
        assert resp.json()["tasks_created"] == 3
