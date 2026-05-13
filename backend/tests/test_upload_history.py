"""
TDD — Upload History feature.
Written before router implementation (red → green after router is complete).

Covers:
  GET /api/v1/upload/history        — 6 tests  (TestUploadHistory)
  POST /api/v1/upload overlap check — 6 tests  (TestUploadOverlapDetection)
  POST /api/v1/upload log insertion — 4 tests  (TestUploadLogInsertion)
"""
from datetime import date, datetime
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.models.staff import Staff
from app.models.upload_log import UploadLog
from app.services.auth_service import AuthService


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


def make_upload_log(
    log_id=1,
    store_id=8901,
    staff_id=1,
    filename="sap_export.csv",
    row_count=27,
    tasks_created=27,
    date_range_start=date(2026, 1, 1),
    date_range_end=date(2026, 3, 31),
    status="success",
):
    log = MagicMock(spec=UploadLog)
    log.id = log_id
    log.store_id = store_id
    log.staff_id = staff_id
    log.filename = filename
    log.uploaded_at = datetime(2026, 5, 1, 10, 0, 0)
    log.row_count = row_count
    log.tasks_created = tasks_created
    log.date_range_start = date_range_start
    log.date_range_end = date_range_end
    log.status = status
    return log


def mock_db_with_staff(staff):
    def _override():
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = staff
        yield db
    return _override


UPLOAD_FILE = {"file": ("sap.csv", b"header\nrow", "text/csv")}


# ---------------------------------------------------------------------------
# GET /api/v1/upload/history
# ---------------------------------------------------------------------------

class TestUploadHistory:

    def test_no_token_returns_403(self):
        client = TestClient(app)
        assert client.get("/api/v1/upload/history").status_code == 403

    def test_associate_returns_403(self):
        """sales_associate JWT must be rejected — manager-only endpoint."""
        app.dependency_overrides[get_db] = mock_db_with_staff(
            make_staff(role="sales_associate")
        )
        client = TestClient(app)
        resp = client.get(
            "/api/v1/upload/history",
            headers=bearer(role="sales_associate"),
        )
        app.dependency_overrides.clear()
        assert resp.status_code == 403

    def test_manager_gets_store_history(self):
        """200 with list; every UploadLog field from openapi.yaml is present."""
        manager = make_staff(role="store_manager", staff_id=2)
        app.dependency_overrides[get_db] = mock_db_with_staff(manager)
        client = TestClient(app)

        log = make_upload_log()
        with patch("app.routers.upload.upload_log_repo") as mock_repo:
            mock_repo.get_by_store.return_value = [log]
            resp = client.get(
                "/api/v1/upload/history",
                headers=bearer(role="store_manager", staff_id=2),
            )

        app.dependency_overrides.clear()
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list) and len(data) == 1
        for field in [
            "id", "store_id", "staff_id", "filename", "uploaded_at",
            "row_count", "tasks_created", "date_range_start", "date_range_end", "status",
        ]:
            assert field in data[0], f"Missing field: {field}"

    def test_manager_only_sees_own_store(self):
        """get_by_store must receive the manager's store_id from their JWT."""
        manager = make_staff(role="store_manager", staff_id=2, store_id=8901)
        app.dependency_overrides[get_db] = mock_db_with_staff(manager)
        client = TestClient(app)

        with patch("app.routers.upload.upload_log_repo") as mock_repo:
            mock_repo.get_by_store.return_value = []
            client.get(
                "/api/v1/upload/history",
                headers=bearer(role="store_manager", staff_id=2, store_id=8901),
            )
            mock_repo.get_by_store.assert_called_once()
            args, kwargs = mock_repo.get_by_store.call_args
            store_id_passed = kwargs.get("store_id") or args[1]
            assert store_id_passed == 8901

        app.dependency_overrides.clear()

    def test_history_ordered_newest_first(self):
        """Ordering is the repo's responsibility; router passes the result through."""
        manager = make_staff(role="store_manager", staff_id=2)
        app.dependency_overrides[get_db] = mock_db_with_staff(manager)
        client = TestClient(app)

        logs = [make_upload_log(log_id=2), make_upload_log(log_id=1)]
        with patch("app.routers.upload.upload_log_repo") as mock_repo:
            mock_repo.get_by_store.return_value = logs
            resp = client.get(
                "/api/v1/upload/history",
                headers=bearer(role="store_manager", staff_id=2),
            )

        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert [item["id"] for item in resp.json()] == [2, 1]

    def test_empty_history_returns_empty_list(self):
        """No logs in DB → [] with 200."""
        manager = make_staff(role="store_manager", staff_id=2)
        app.dependency_overrides[get_db] = mock_db_with_staff(manager)
        client = TestClient(app)

        with patch("app.routers.upload.upload_log_repo") as mock_repo:
            mock_repo.get_by_store.return_value = []
            resp = client.get(
                "/api/v1/upload/history",
                headers=bearer(role="store_manager", staff_id=2),
            )

        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert resp.json() == []


# ---------------------------------------------------------------------------
# POST /api/v1/upload — overlap detection
# ---------------------------------------------------------------------------

class TestUploadOverlapDetection:

    def _make_parse_result(self, posting_dates=None):
        if posting_dates is None:
            posting_dates = [date(2026, 4, 1), date(2026, 4, 30)]
        parse_result = MagicMock()
        parse_result.records = [
            {
                "idoc_number": f"IDOC{i}",
                "posting_date": d,
                "customer_id": "C001",
                "ean": None,
                "material_desc": None,
            }
            for i, d in enumerate(posting_dates)
        ]
        parse_result.errors = []
        return parse_result

    def test_no_overlap_returns_200(self):
        """No existing overlap → processes normally."""
        staff = make_staff()
        app.dependency_overrides[get_db] = mock_db_with_staff(staff)
        client = TestClient(app)

        with patch("app.routers.upload.staff_repo") as mock_staff_repo, \
             patch("app.routers.upload.SAPParser") as mock_parser, \
             patch("app.routers.upload.transaction_repo"), \
             patch("app.routers.upload.CycleReset") as mock_reset, \
             patch("app.routers.upload.upload_log_repo") as mock_log_repo:

            mock_staff_repo.get_by_id.return_value = staff
            mock_parser.return_value.parse.return_value = self._make_parse_result()
            mock_reset.run.return_value = MagicMock(tasks_created=3, cycles_reset=1)
            mock_log_repo.find_overlap.return_value = None

            resp = client.post("/api/v1/upload", files=UPLOAD_FILE, headers=bearer())

        app.dependency_overrides.clear()
        assert resp.status_code == 200

    def test_exact_overlap_returns_409_with_conflict_payload(self):
        """Date range matches existing log → 409 with full conflict payload."""
        staff = make_staff()
        app.dependency_overrides[get_db] = mock_db_with_staff(staff)
        client = TestClient(app)

        existing = make_upload_log(filename="old.csv")
        with patch("app.routers.upload.staff_repo") as mock_staff_repo, \
             patch("app.routers.upload.SAPParser") as mock_parser, \
             patch("app.routers.upload.upload_log_repo") as mock_log_repo:

            mock_staff_repo.get_by_id.return_value = staff
            mock_parser.return_value.parse.return_value = self._make_parse_result()
            mock_log_repo.find_overlap.return_value = existing

            resp = client.post("/api/v1/upload", files=UPLOAD_FILE, headers=bearer())

        app.dependency_overrides.clear()
        assert resp.status_code == 409
        data = resp.json()
        assert data["conflict"] is True
        ou = data["overlapping_upload"]
        assert "filename" in ou
        assert "uploaded_at" in ou
        assert "date_range" in ou

    def test_partial_overlap_new_start_inside_existing_returns_409(self):
        """New start falls inside existing range → 409."""
        staff = make_staff()
        app.dependency_overrides[get_db] = mock_db_with_staff(staff)
        client = TestClient(app)

        existing = make_upload_log(
            date_range_start=date(2026, 3, 1),
            date_range_end=date(2026, 4, 15),
        )
        with patch("app.routers.upload.staff_repo") as mock_staff_repo, \
             patch("app.routers.upload.SAPParser") as mock_parser, \
             patch("app.routers.upload.upload_log_repo") as mock_log_repo:

            mock_staff_repo.get_by_id.return_value = staff
            mock_parser.return_value.parse.return_value = self._make_parse_result(
                [date(2026, 4, 1), date(2026, 4, 30)]
            )
            mock_log_repo.find_overlap.return_value = existing

            resp = client.post("/api/v1/upload", files=UPLOAD_FILE, headers=bearer())

        app.dependency_overrides.clear()
        assert resp.status_code == 409

    def test_partial_overlap_new_end_inside_existing_returns_409(self):
        """New end falls inside existing range → 409."""
        staff = make_staff()
        app.dependency_overrides[get_db] = mock_db_with_staff(staff)
        client = TestClient(app)

        existing = make_upload_log(
            date_range_start=date(2026, 4, 15),
            date_range_end=date(2026, 5, 31),
        )
        with patch("app.routers.upload.staff_repo") as mock_staff_repo, \
             patch("app.routers.upload.SAPParser") as mock_parser, \
             patch("app.routers.upload.upload_log_repo") as mock_log_repo:

            mock_staff_repo.get_by_id.return_value = staff
            mock_parser.return_value.parse.return_value = self._make_parse_result(
                [date(2026, 4, 1), date(2026, 4, 30)]
            )
            mock_log_repo.find_overlap.return_value = existing

            resp = client.post("/api/v1/upload", files=UPLOAD_FILE, headers=bearer())

        app.dependency_overrides.clear()
        assert resp.status_code == 409

    def test_force_true_bypasses_overlap_and_returns_200(self):
        """?force=true with existing overlap → skips check, returns 200."""
        staff = make_staff()
        app.dependency_overrides[get_db] = mock_db_with_staff(staff)
        client = TestClient(app)

        with patch("app.routers.upload.staff_repo") as mock_staff_repo, \
             patch("app.routers.upload.SAPParser") as mock_parser, \
             patch("app.routers.upload.transaction_repo") as mock_txn_repo, \
             patch("app.routers.upload.CycleReset") as mock_reset, \
             patch("app.routers.upload.upload_log_repo") as mock_log_repo:

            mock_staff_repo.get_by_id.return_value = staff
            mock_parser.return_value.parse.return_value = self._make_parse_result()
            mock_txn_repo.upsert.return_value = (MagicMock(), True)
            mock_reset.run.return_value = MagicMock(tasks_created=3, cycles_reset=1)
            mock_log_repo.find_overlap.return_value = make_upload_log()

            resp = client.post(
                "/api/v1/upload?force=true",
                files=UPLOAD_FILE,
                headers=bearer(),
            )

        app.dependency_overrides.clear()
        assert resp.status_code == 200
        mock_log_repo.find_overlap.assert_not_called()

    def test_force_false_with_overlap_returns_409(self):
        """Explicit ?force=false with overlap → same as default, 409."""
        staff = make_staff()
        app.dependency_overrides[get_db] = mock_db_with_staff(staff)
        client = TestClient(app)

        with patch("app.routers.upload.staff_repo") as mock_staff_repo, \
             patch("app.routers.upload.SAPParser") as mock_parser, \
             patch("app.routers.upload.upload_log_repo") as mock_log_repo:

            mock_staff_repo.get_by_id.return_value = staff
            mock_parser.return_value.parse.return_value = self._make_parse_result()
            mock_log_repo.find_overlap.return_value = make_upload_log()

            resp = client.post(
                "/api/v1/upload?force=false",
                files=UPLOAD_FILE,
                headers=bearer(),
            )

        app.dependency_overrides.clear()
        assert resp.status_code == 409


# ---------------------------------------------------------------------------
# POST /api/v1/upload — log insertion behavior
# ---------------------------------------------------------------------------

class TestUploadLogInsertion:

    def _run_upload(self, staff, parse_result, mock_log_repo, url="/api/v1/upload"):
        app.dependency_overrides[get_db] = mock_db_with_staff(staff)
        client = TestClient(app)

        with patch("app.routers.upload.staff_repo") as mock_staff_repo, \
             patch("app.routers.upload.SAPParser") as mock_parser, \
             patch("app.routers.upload.transaction_repo"), \
             patch("app.routers.upload.CycleReset") as mock_reset, \
             patch("app.routers.upload.upload_log_repo", mock_log_repo):

            mock_staff_repo.get_by_id.return_value = staff
            mock_parser.return_value.parse.return_value = parse_result
            mock_reset.run.return_value = MagicMock(tasks_created=3, cycles_reset=1)
            mock_log_repo.find_overlap.return_value = None

            resp = client.post(url, files=UPLOAD_FILE, headers=bearer())

        app.dependency_overrides.clear()
        return resp

    def test_successful_upload_inserts_log(self):
        """upload_log_repo.create called once with correct store_id, staff_id, status."""
        staff = make_staff(staff_id=1, store_id=8901)
        parse_result = MagicMock()
        parse_result.records = [
            {"idoc_number": "IDOC1", "posting_date": date(2026, 4, 10),
             "customer_id": "C001", "ean": None, "material_desc": None},
        ]
        parse_result.errors = []

        mock_log_repo = MagicMock()
        mock_log_repo.find_overlap.return_value = None

        resp = self._run_upload(staff, parse_result, mock_log_repo)

        assert resp.status_code == 200
        mock_log_repo.create.assert_called_once()
        kw = mock_log_repo.create.call_args.kwargs
        assert kw["store_id"] == 8901
        assert kw["staff_id"] == 1
        assert kw["status"] == "success"

    def test_parse_error_does_not_insert_log(self):
        """SAPParseError → 400, no log row created."""
        staff = make_staff()
        app.dependency_overrides[get_db] = mock_db_with_staff(staff)
        client = TestClient(app)

        mock_log_repo = MagicMock()

        with patch("app.routers.upload.staff_repo") as mock_staff_repo, \
             patch("app.routers.upload.SAPParser") as mock_parser, \
             patch("app.routers.upload.upload_log_repo", mock_log_repo):

            mock_staff_repo.get_by_id.return_value = staff
            from app.services.sap_parser import SAPParseError
            mock_parser.return_value.parse.side_effect = SAPParseError("bad file")

            resp = client.post("/api/v1/upload", files=UPLOAD_FILE, headers=bearer())

        app.dependency_overrides.clear()
        assert resp.status_code == 400
        mock_log_repo.create.assert_not_called()

    def test_log_date_range_is_min_max_of_posting_dates(self):
        """date_range_start = earliest posting_date, date_range_end = latest."""
        staff = make_staff(staff_id=1, store_id=8901)
        parse_result = MagicMock()
        parse_result.records = [
            {"idoc_number": "IDOC1", "posting_date": date(2026, 3, 15),
             "customer_id": "C001", "ean": None, "material_desc": None},
            {"idoc_number": "IDOC2", "posting_date": date(2026, 1, 5),
             "customer_id": "C002", "ean": None, "material_desc": None},
            {"idoc_number": "IDOC3", "posting_date": date(2026, 4, 20),
             "customer_id": "C003", "ean": None, "material_desc": None},
        ]
        parse_result.errors = []

        mock_log_repo = MagicMock()
        mock_log_repo.find_overlap.return_value = None

        resp = self._run_upload(staff, parse_result, mock_log_repo)

        assert resp.status_code == 200
        kw = mock_log_repo.create.call_args.kwargs
        assert kw["date_range_start"] == date(2026, 1, 5)
        assert kw["date_range_end"] == date(2026, 4, 20)

    def test_db_exception_does_not_insert_log(self):
        """Exception during processing → 500, rollback, no log inserted."""
        staff = make_staff()
        app.dependency_overrides[get_db] = mock_db_with_staff(staff)
        client = TestClient(app)

        parse_result = MagicMock()
        parse_result.records = [
            {"idoc_number": "IDOC1", "posting_date": date(2026, 4, 1),
             "customer_id": "C001", "ean": None, "material_desc": None},
        ]
        parse_result.errors = []

        mock_log_repo = MagicMock()
        mock_log_repo.find_overlap.return_value = None

        with patch("app.routers.upload.staff_repo") as mock_staff_repo, \
             patch("app.routers.upload.SAPParser") as mock_parser, \
             patch("app.routers.upload.transaction_repo") as mock_txn_repo, \
             patch("app.routers.upload.upload_log_repo", mock_log_repo):

            mock_staff_repo.get_by_id.return_value = staff
            mock_parser.return_value.parse.return_value = parse_result
            mock_txn_repo.create.side_effect = Exception("DB connection lost")

            resp = client.post("/api/v1/upload", files=UPLOAD_FILE, headers=bearer())

        app.dependency_overrides.clear()
        assert resp.status_code == 500
        mock_log_repo.create.assert_not_called()
