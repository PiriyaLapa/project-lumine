"""
TDD — diagnostic logging on GET /api/v1/tasks (GH #29).

No confirmed root cause exists yet for the empty-Dashboard-on-cold-start
symptom (frontend JWT-race and backend query/scheduling-timing theories
were both investigated and ruled out). This adds a per-call INFO log
(staff_id, role, store_id, count) so that if the symptom recurs, Render's
log stream shows the actual request shape instead of requiring guesswork.

Written before implementation — red until app/routers/tasks.py is updated.
Mirrors test_customer_name_on_tasks.py's mocking pattern.
"""
import logging
from datetime import date
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.models.follow_up_task import FollowUpTask
from app.models.staff import Staff
from app.services.auth_service import AuthService


# ---------------------------------------------------------------------------
# Helpers (mirrors test_customer_name_on_tasks.py)
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


def make_task_row(task_id=1, status="Pending", staff_name="Benz", customer_name="Somchai Jaidee"):
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
    return (t, staff_name, customer_name)


def mock_db_with_staff(staff):
    def _override():
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = staff
        yield db
    return _override


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGetTasksLogging:

    def test_associate_call_logs_staff_role_store_and_count(self, caplog):
        staff = make_staff(role="sales_associate", staff_id=1, store_id=8901)
        app.dependency_overrides[get_db] = mock_db_with_staff(staff)
        client = TestClient(app)

        with patch("app.routers.tasks.task_repo") as mock_repo:
            mock_repo.get_tasks_for_staff.return_value = [
                make_task_row(task_id=1), make_task_row(task_id=2),
            ]
            with caplog.at_level(logging.INFO, logger="app.routers.tasks"):
                resp = client.get("/api/v1/tasks", headers=bearer(staff_id=1, store_id=8901))

        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert "staff=1" in caplog.text
        assert "role=sales_associate" in caplog.text
        assert "store_id=8901" in caplog.text
        assert "count=2" in caplog.text

    def test_manager_call_logs_via_store_branch(self, caplog):
        manager = make_staff(role="store_manager", staff_id=2, store_id=8901)
        app.dependency_overrides[get_db] = mock_db_with_staff(manager)
        client = TestClient(app)

        with patch("app.routers.tasks.task_repo") as mock_repo:
            mock_repo.get_tasks_for_store.return_value = [make_task_row(task_id=1)]
            with caplog.at_level(logging.INFO, logger="app.routers.tasks"):
                resp = client.get(
                    "/api/v1/tasks", headers=bearer(role="store_manager", staff_id=2, store_id=8901)
                )

        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert "staff=2" in caplog.text
        assert "role=store_manager" in caplog.text
        assert "store_id=8901" in caplog.text
        assert "count=1" in caplog.text

    def test_empty_result_logs_count_zero(self, caplog):
        """The exact log line we'd want to see if GH #29 recurs."""
        staff = make_staff(role="sales_associate", staff_id=1, store_id=8901)
        app.dependency_overrides[get_db] = mock_db_with_staff(staff)
        client = TestClient(app)

        with patch("app.routers.tasks.task_repo") as mock_repo:
            mock_repo.get_tasks_for_staff.return_value = []
            with caplog.at_level(logging.INFO, logger="app.routers.tasks"):
                resp = client.get("/api/v1/tasks", headers=bearer(staff_id=1, store_id=8901))

        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert resp.json() == []
        assert "count=0" in caplog.text
        assert "staff=1" in caplog.text
