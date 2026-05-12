"""
TDD — staff_name field on GET /api/v1/tasks.
Written before implementation — red until task_repo + router are updated.

After the repo returns (FollowUpTask, staff_name) tuples, these turn green.
"""
from datetime import date
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.models.follow_up_task import FollowUpTask
from app.models.staff import Staff
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


def make_task_row(task_id=1, status="Pending", staff_name="Benz"):
    """(FollowUpTask mock, staff_name) — matches new repo return shape."""
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
    return (t, staff_name)


def mock_db_with_staff(staff):
    def _override():
        db = MagicMock()
        db.query.return_value.filter.return_value.first.return_value = staff
        yield db
    return _override


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestStaffNameOnTasks:

    def test_associate_tasks_include_staff_name(self):
        """GET /tasks for associate includes staff_name on each item."""
        staff = make_staff(role="sales_associate", staff_id=1)
        app.dependency_overrides[get_db] = mock_db_with_staff(staff)
        client = TestClient(app)

        with patch("app.routers.tasks.task_repo") as mock_repo:
            mock_repo.get_tasks_for_staff.return_value = [make_task_row(staff_name="Benz")]
            resp = client.get("/api/v1/tasks", headers=bearer())

        app.dependency_overrides.clear()
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert "staff_name" in data[0], "staff_name missing from response"
        assert data[0]["staff_name"] == "Benz"

    def test_manager_tasks_include_correct_staff_names(self):
        """GET /tasks for manager returns the correct staff_name per task."""
        manager = make_staff(role="store_manager", staff_id=2, store_id=8901)
        app.dependency_overrides[get_db] = mock_db_with_staff(manager)
        client = TestClient(app)

        rows = [
            make_task_row(task_id=1, staff_name="Benz"),
            make_task_row(task_id=2, staff_name="Ann"),
        ]
        with patch("app.routers.tasks.task_repo") as mock_repo:
            mock_repo.get_tasks_for_store.return_value = rows
            resp = client.get("/api/v1/tasks", headers=bearer(role="store_manager", staff_id=2))

        app.dependency_overrides.clear()
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["staff_name"] == "Benz"
        assert data[1]["staff_name"] == "Ann"

    def test_staff_name_is_a_string(self):
        """staff_name must be a plain string — not null, not int."""
        staff = make_staff()
        app.dependency_overrides[get_db] = mock_db_with_staff(staff)
        client = TestClient(app)

        with patch("app.routers.tasks.task_repo") as mock_repo:
            mock_repo.get_tasks_for_staff.return_value = [make_task_row(staff_name="Benz")]
            resp = client.get("/api/v1/tasks", headers=bearer())

        app.dependency_overrides.clear()
        assert isinstance(resp.json()[0]["staff_name"], str)

    def test_all_openapi_fields_present_including_staff_name(self):
        """Full openapi.yaml FollowUpTask field set must be present."""
        staff = make_staff()
        app.dependency_overrides[get_db] = mock_db_with_staff(staff)
        client = TestClient(app)

        with patch("app.routers.tasks.task_repo") as mock_repo:
            mock_repo.get_tasks_for_staff.return_value = [make_task_row(staff_name="Benz")]
            resp = client.get("/api/v1/tasks", headers=bearer())

        app.dependency_overrides.clear()
        data = resp.json()
        for field in [
            "id", "customer_id", "task_type", "task_basis",
            "due_date", "calculated_from", "status",
            "staff_name", "created_at", "updated_at",
        ]:
            assert field in data[0], f"Missing field: {field}"
