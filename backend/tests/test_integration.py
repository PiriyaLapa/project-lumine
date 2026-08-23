"""
Integration Playbook — Step 5.
End-to-end HTTP tests against all endpoints defined in openapi.yaml.
Uses FastAPI TestClient + mocked DB + mocked services (no real MySQL / Drive).

Verifies:
  - Correct HTTP status codes
  - Response field names match openapi.yaml exactly
  - Auth enforcement (no token → 403/401)
  - Role-based routing (associate vs manager)
"""
import io
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.services.auth_service import AuthService
from app.models.staff import Staff
from app.models.follow_up_task import FollowUpTask
from datetime import date


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_staff(role="sales_associate", staff_id=1, store_id=5):
    s = Staff()
    s.id = staff_id
    s.name = "Benz"
    s.employee_code = "EMP001"
    s.role = role
    s.store_id = store_id
    s.email = "benz@lumine.com"
    s.hashed_password = AuthService.hash_password("secret")
    s.deleted_at = None
    return s


def bearer(role="sales_associate", staff_id=1, store_id=5):
    token = AuthService.create_access_token(
        {"staff_id": staff_id, "role": role, "store_id": store_id}
    )
    return {"Authorization": f"Bearer {token}"}


def make_task(task_id=1, status="Pending"):
    t = MagicMock(spec=FollowUpTask)
    t.id = task_id
    t.customer_id = "CUST001"
    t.task_type = "2D"
    t.task_basis = "posting_date"
    t.due_date = date(2026, 5, 1)
    t.calculated_from = date(2026, 4, 29)
    t.status = status
    t.created_at = "2026-04-19 00:00:00"
    t.updated_at = "2026-04-19 00:00:00"
    t.idoc_number = "IDOC001"
    return t


def mock_db_with_staff(staff):
    def _override():
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = staff
        yield db
    return _override


# ---------------------------------------------------------------------------
# /api/v1/upload — POST
# ---------------------------------------------------------------------------

class TestUploadEndpoint:
    def test_no_token_returns_403(self):
        client = TestClient(app)
        resp = client.post("/api/v1/upload", files={"file": ("test.csv", b"data", "text/csv")})
        assert resp.status_code == 403

    def test_valid_upload_returns_expected_fields(self):
        """Response must contain tasks_created, customers_processed, cycles_reset, errors."""
        staff = make_staff()
        app.dependency_overrides[get_db] = mock_db_with_staff(staff)
        client = TestClient(app)

        with patch("app.routers.upload.staff_repo") as mock_staff_repo, \
             patch("app.routers.upload.SAPParser") as mock_parser, \
             patch("app.routers.upload.transaction_repo") as mock_txn_repo, \
             patch("app.routers.upload.CycleReset") as mock_reset:

            mock_staff_repo.get_by_id.return_value = staff
            parse_result = MagicMock()
            parse_result.records = []
            parse_result.errors = []
            mock_parser.return_value.parse.return_value = parse_result
            mock_reset.run.return_value = MagicMock(tasks_created=0, cycles_reset=0)

            resp = client.post(
                "/api/v1/upload",
                files={"file": ("test.csv", b"header\nrow", "text/csv")},
                headers=bearer(),
            )

        app.dependency_overrides.clear()

        assert resp.status_code == 200
        data = resp.json()
        for field in ["tasks_created", "customers_processed", "cycles_reset", "errors"]:
            assert field in data, f"Missing field: {field}"

    def test_malformed_sap_file_returns_400(self):
        staff = make_staff()
        app.dependency_overrides[get_db] = mock_db_with_staff(staff)
        client = TestClient(app)

        with patch("app.routers.upload.staff_repo") as mock_staff_repo, \
             patch("app.routers.upload.SAPParser") as mock_parser:

            mock_staff_repo.get_by_id.return_value = staff
            from app.services.sap_parser import SAPParseError
            mock_parser.return_value.parse.side_effect = SAPParseError("bad file")

            resp = client.post(
                "/api/v1/upload",
                files={"file": ("bad.csv", b"garbage", "text/csv")},
                headers=bearer(),
            )

        app.dependency_overrides.clear()
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# /api/v1/tasks — GET
# ---------------------------------------------------------------------------

class TestTasksEndpoint:
    def test_no_token_returns_403(self):
        client = TestClient(app)
        assert client.get("/api/v1/tasks").status_code == 403

    def test_associate_gets_own_tasks(self):
        """GET /tasks returns list; each item has openapi.yaml FollowUpTask fields."""
        app.dependency_overrides[get_db] = mock_db_with_staff(make_staff())
        client = TestClient(app)

        task = make_task()
        with patch("app.routers.tasks.task_repo") as mock_repo:
            mock_repo.get_tasks_for_staff.return_value = [(task, "Benz", "Somchai Jaidee")]
            resp = client.get("/api/v1/tasks", headers=bearer())

        app.dependency_overrides.clear()

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        for field in ["id", "customer_id", "task_type", "task_basis",
                      "due_date", "calculated_from", "status", "staff_name",
                      "customer_name", "created_at", "updated_at"]:
            assert field in data[0], f"Missing field: {field}"

    def test_manager_gets_store_tasks(self):
        """store_manager role triggers get_tasks_for_store, not get_tasks_for_staff."""
        manager = make_staff(role="store_manager", staff_id=2)
        app.dependency_overrides[get_db] = mock_db_with_staff(manager)
        client = TestClient(app)

        with patch("app.routers.tasks.task_repo") as mock_repo:
            mock_repo.get_tasks_for_store.return_value = [(make_task(), "Benz", "Somchai Jaidee")]
            resp = client.get("/api/v1/tasks", headers=bearer(role="store_manager", staff_id=2))

            mock_repo.get_tasks_for_store.assert_called_once()
            mock_repo.get_tasks_for_staff.assert_not_called()

        app.dependency_overrides.clear()
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# /api/v1/tasks/{task_id} — PATCH
# ---------------------------------------------------------------------------

class TestTaskPatchEndpoint:
    def test_no_token_returns_403(self):
        client = TestClient(app)
        assert client.patch("/api/v1/tasks/1", json={"status": "Done"}).status_code == 403

    def test_mark_done_returns_updated_task(self):
        """PATCH returns FollowUpTask with status=Done."""
        from app.models.transaction import Transaction as TxnModel
        client = TestClient(app)

        task = make_task(status="Pending")
        done_task = make_task(status="Done")
        fake_txn = MagicMock()
        fake_txn.staff_id = 1
        fake_txn.idoc_number = "IDOC001"

        def fake_override():
            db = MagicMock()
            # Return correct type per query model
            def query_side_effect(model):
                chain = MagicMock()
                if model is TxnModel:
                    chain.filter.return_value.first.return_value = fake_txn
                else:
                    chain.filter.return_value.first.return_value = None
                return chain
            db.query.side_effect = query_side_effect
            yield db

        app.dependency_overrides[get_db] = fake_override

        with patch("app.routers.tasks.task_repo") as mock_repo:
            mock_repo.get_by_id.return_value = task
            mock_repo.mark_done.return_value = done_task
            mock_repo.get_staff_name_for_task.return_value = "Benz"
            mock_repo.get_customer_name_for_task.return_value = "Somchai Jaidee"
            resp = client.patch(
                "/api/v1/tasks/1",
                json={"status": "Done"},
                headers=bearer(),
            )

        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert resp.json()["status"] == "Done"

    def test_invalid_status_returns_422(self):
        """Only 'Done' is accepted. Anything else → 422."""
        app.dependency_overrides[get_db] = mock_db_with_staff(make_staff())
        client = TestClient(app)
        resp = client.patch("/api/v1/tasks/1", json={"status": "Superseded"}, headers=bearer())
        app.dependency_overrides.clear()
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# /api/v1/evidence — POST
# ---------------------------------------------------------------------------

class TestEvidenceEndpoint:
    def test_no_token_returns_403(self):
        client = TestClient(app)
        resp = client.post("/api/v1/evidence", data={"task_id": 1, "notes": "test"})
        assert resp.status_code == 403

    def test_notes_only_returns_expected_fields(self):
        """POST /evidence with notes only (no image) — response matches openapi.yaml."""
        app.dependency_overrides[get_db] = mock_db_with_staff(make_staff())
        client = TestClient(app)

        mock_result = MagicMock()
        mock_result.id = 10
        mock_result.notes = "Customer was happy."
        mock_result.image_uri = None
        mock_result.image_size_kb = None
        mock_result.timestamp = "2026-04-19 12:00:00"
        mock_result.drive_failed = False

        with patch("app.routers.evidence.EvidenceService.save", return_value=mock_result):
            resp = client.post(
                "/api/v1/evidence",
                data={"task_id": "1", "notes": "Customer was happy."},
                headers=bearer(),
            )

        app.dependency_overrides.clear()

        assert resp.status_code == 200
        data = resp.json()
        for field in ["id", "task_id", "notes", "image_uri", "image_size_kb", "timestamp"]:
            assert field in data, f"Missing field: {field}"
        assert "drive_failed" not in data, "drive_failed must NOT be in response (not in openapi.yaml)"
        assert data["id"] == 10
        assert data["task_id"] == 1
        assert data["notes"] == "Customer was happy."
        assert data["image_uri"] is None

    def test_image_over_800kb_returns_413(self):
        """Backend rejects images over 800KB with 413."""
        app.dependency_overrides[get_db] = mock_db_with_staff(make_staff())
        client = TestClient(app)

        large_image = b"\xff\xd8\xff\xe0" + b"\x00" * (900 * 1024)

        with patch("app.routers.evidence.EvidenceService.save",
                   side_effect=ValueError("800KB limit")):
            resp = client.post(
                "/api/v1/evidence",
                data={"task_id": "1", "notes": ""},
                files={"image": ("evidence.jpg", large_image, "image/jpeg")},
                headers=bearer(),
            )

        app.dependency_overrides.clear()
        assert resp.status_code == 413


# ---------------------------------------------------------------------------
# /api/v1/reports/kpi — GET
# ---------------------------------------------------------------------------

class TestKPIEndpoint:
    def test_no_token_returns_403(self):
        client = TestClient(app)
        assert client.get("/api/v1/reports/kpi").status_code == 403

    def test_associate_kpi_returns_expected_fields(self):
        """GET /reports/kpi returns KPIReport matching openapi.yaml schema."""
        app.dependency_overrides[get_db] = mock_db_with_staff(make_staff())
        client = TestClient(app)

        from app.services.report_service import KPIResult
        mock_result = KPIResult(
            staff_id=1, store_id=5, total_tasks=10, completed_tasks=7,
            completion_rate=0.7
        )

        with patch("app.routers.reports.ReportService.get_kpi_for_staff", return_value=mock_result):
            resp = client.get("/api/v1/reports/kpi", headers=bearer())

        app.dependency_overrides.clear()

        assert resp.status_code == 200
        data = resp.json()
        for field in ["staff_id", "store_id", "total_tasks", "completed_tasks", "completion_rate"]:
            assert field in data, f"Missing field: {field}"
        assert data["completion_rate"] == pytest.approx(0.7)

    def test_manager_calls_store_kpi(self):
        """store_manager role triggers get_kpi_for_store."""
        manager = make_staff(role="store_manager", staff_id=2)
        app.dependency_overrides[get_db] = mock_db_with_staff(manager)
        client = TestClient(app)

        from app.services.report_service import KPIResult
        mock_result = KPIResult(
            staff_id=None, store_id=5, total_tasks=50, completed_tasks=40,
            completion_rate=0.8
        )

        with patch("app.routers.reports.ReportService.get_kpi_for_store", return_value=mock_result) as mock_store, \
             patch("app.routers.reports.ReportService.get_kpi_for_staff") as mock_staff:
            resp = client.get(
                "/api/v1/reports/kpi",
                headers=bearer(role="store_manager", staff_id=2),
            )
            mock_store.assert_called_once()
            mock_staff.assert_not_called()

        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert resp.json()["staff_id"] is None


class TestManagerDashboardEndpoint:
    def _make_result(self, store_id, staff_breakdown):
        from app.services.dashboard_service import DashboardResult
        return DashboardResult(
            store_id=store_id, period="today", date_from=date(2026, 7, 21), date_to=date(2026, 7, 21),
            staff_breakdown=staff_breakdown,
            store_totals=staff_breakdown[0] if len(staff_breakdown) == 1 else staff_breakdown[-1],
        )

    def _make_stats(self, staff_id=1, staff_name="Jane"):
        from app.services.dashboard_service import StaffFollowUpStats
        return StaffFollowUpStats(
            staff_id=staff_id, staff_name=staff_name, tasks_due=5, tasks_done=3,
            tasks_pending=2, tasks_skipped=0, messages_sent_line=2, messages_sent_email=1,
            customers_followed_up=3,
        )

    def test_no_token_returns_403(self):
        client = TestClient(app)
        assert client.get("/api/v1/reports/dashboard").status_code == 403

    def test_associate_gets_200_with_single_row_breakdown(self):
        app.dependency_overrides[get_db] = mock_db_with_staff(make_staff())
        client = TestClient(app)

        own_row = self._make_stats(staff_id=1, staff_name="Benz")
        result = self._make_result(store_id=5, staff_breakdown=[own_row])

        with patch("app.routers.reports.DashboardService.get_staff_dashboard", return_value=result) as mock_staff:
            resp = client.get("/api/v1/reports/dashboard", headers=bearer())
            mock_staff.assert_called_once()

        app.dependency_overrides.clear()
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["staff_breakdown"]) == 1
        for field in [
            "staff_id", "staff_name", "tasks_due", "tasks_done", "tasks_pending",
            "tasks_skipped", "messages_sent_line", "messages_sent_email", "customers_followed_up",
        ]:
            assert field in data["store_totals"], f"Missing field: {field}"

    def test_manager_gets_200_with_multi_row_breakdown(self):
        manager = make_staff(role="store_manager", staff_id=2)
        app.dependency_overrides[get_db] = mock_db_with_staff(manager)
        client = TestClient(app)

        breakdown = [self._make_stats(staff_id=1, staff_name="Jane"), self._make_stats(staff_id=2, staff_name="John")]
        result = self._make_result(store_id=5, staff_breakdown=breakdown)

        with patch("app.routers.reports.DashboardService.get_manager_dashboard", return_value=result) as mock_mgr, \
             patch("app.routers.reports.DashboardService.get_staff_dashboard") as mock_staff:
            resp = client.get(
                "/api/v1/reports/dashboard", headers=bearer(role="store_manager", staff_id=2)
            )
            mock_mgr.assert_called_once()
            mock_staff.assert_not_called()

        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert len(resp.json()["staff_breakdown"]) == 2

    def test_default_period_is_today(self):
        app.dependency_overrides[get_db] = mock_db_with_staff(make_staff())
        client = TestClient(app)

        result = self._make_result(store_id=5, staff_breakdown=[self._make_stats()])
        with patch("app.routers.reports.DashboardService.get_staff_dashboard", return_value=result) as mock_staff:
            client.get("/api/v1/reports/dashboard", headers=bearer())
            assert mock_staff.call_args.kwargs["period"] == "today"

        app.dependency_overrides.clear()

    def test_invalid_period_returns_422(self):
        app.dependency_overrides[get_db] = mock_db_with_staff(make_staff())
        client = TestClient(app)
        resp = client.get("/api/v1/reports/dashboard?period=year", headers=bearer())
        app.dependency_overrides.clear()
        assert resp.status_code == 422

    def test_manager_scoped_to_own_store_id(self):
        manager = make_staff(role="store_manager", staff_id=2, store_id=9)
        app.dependency_overrides[get_db] = mock_db_with_staff(manager)
        client = TestClient(app)

        result = self._make_result(store_id=9, staff_breakdown=[self._make_stats()])
        with patch("app.routers.reports.DashboardService.get_manager_dashboard", return_value=result) as mock_mgr:
            client.get("/api/v1/reports/dashboard", headers=bearer(role="store_manager", staff_id=2, store_id=9))
            assert mock_mgr.call_args.kwargs["store_id"] == 9

        app.dependency_overrides.clear()
