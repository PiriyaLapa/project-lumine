"""
TDD — customer_name field on GET /api/v1/tasks and PATCH /api/v1/tasks/{id}.
Written before implementation — red until task_repo + router are updated.
Mirrors test_staff_name.py exactly, extended for the new field.

customer_name is sourced from the SAP file's "Customer name" column,
stored on transactions.customer_name (migration 0010) — nullable, same
reasoning as staff_name (null for rows without it in the source file).
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


def make_task_row(task_id=1, status="Pending", staff_name="Benz", customer_name="Somchai Jaidee"):
    """(FollowUpTask mock, staff_name, customer_name) — matches new repo return shape."""
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

class TestCustomerNameOnTasks:

    def test_associate_tasks_include_customer_name(self):
        """GET /tasks for associate includes customer_name on each item."""
        staff = make_staff(role="sales_associate", staff_id=1)
        app.dependency_overrides[get_db] = mock_db_with_staff(staff)
        client = TestClient(app)

        with patch("app.routers.tasks.task_repo") as mock_repo:
            mock_repo.get_tasks_for_staff.return_value = [make_task_row(customer_name="Somchai Jaidee")]
            resp = client.get("/api/v1/tasks", headers=bearer())

        app.dependency_overrides.clear()
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert "customer_name" in data[0], "customer_name missing from response"
        assert data[0]["customer_name"] == "Somchai Jaidee"

    def test_manager_tasks_include_correct_customer_names(self):
        """GET /tasks for manager returns the correct customer_name per task."""
        manager = make_staff(role="store_manager", staff_id=2, store_id=8901)
        app.dependency_overrides[get_db] = mock_db_with_staff(manager)
        client = TestClient(app)

        rows = [
            make_task_row(task_id=1, customer_name="Somchai Jaidee"),
            make_task_row(task_id=2, customer_name="Asia - Others"),
        ]
        with patch("app.routers.tasks.task_repo") as mock_repo:
            mock_repo.get_tasks_for_store.return_value = rows
            resp = client.get("/api/v1/tasks", headers=bearer(role="store_manager", staff_id=2))

        app.dependency_overrides.clear()
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["customer_name"] == "Somchai Jaidee"
        assert data[1]["customer_name"] == "Asia - Others"

    def test_customer_name_is_nullable(self):
        """customer_name must be null-safe — no CRM/SAP name on file for this row."""
        staff = make_staff()
        app.dependency_overrides[get_db] = mock_db_with_staff(staff)
        client = TestClient(app)

        with patch("app.routers.tasks.task_repo") as mock_repo:
            mock_repo.get_tasks_for_staff.return_value = [make_task_row(customer_name=None)]
            resp = client.get("/api/v1/tasks", headers=bearer())

        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert resp.json()[0]["customer_name"] is None

    def test_all_openapi_fields_present_including_customer_name(self):
        """Full openapi.yaml FollowUpTask field set must be present."""
        staff = make_staff()
        app.dependency_overrides[get_db] = mock_db_with_staff(staff)
        client = TestClient(app)

        with patch("app.routers.tasks.task_repo") as mock_repo:
            mock_repo.get_tasks_for_staff.return_value = [make_task_row()]
            resp = client.get("/api/v1/tasks", headers=bearer())

        app.dependency_overrides.clear()
        data = resp.json()
        for field in [
            "id", "customer_id", "task_type", "task_basis",
            "due_date", "calculated_from", "status",
            "staff_name", "customer_name", "created_at", "updated_at",
        ]:
            assert field in data[0], f"Missing field: {field}"

    def test_patch_response_includes_customer_name(self):
        """PATCH /tasks/{id} (Mark as Contacted) response also includes customer_name."""
        staff = make_staff()
        app.dependency_overrides[get_db] = mock_db_with_staff(staff)
        client = TestClient(app)

        task_mock = MagicMock(spec=FollowUpTask)
        task_mock.id = 1
        task_mock.customer_id = "CUST001"
        task_mock.task_type = "2D"
        task_mock.task_basis = "posting_date"
        task_mock.due_date = date(2026, 5, 1)
        task_mock.calculated_from = date(2026, 4, 29)
        task_mock.status = "Pending"
        task_mock.created_at = "2026-04-19 00:00:00"
        task_mock.updated_at = "2026-04-19 00:00:00"
        task_mock.idoc_number = "IDOC001"

        done_mock = MagicMock(spec=FollowUpTask)
        done_mock.id = 1
        done_mock.customer_id = "CUST001"
        done_mock.task_type = "2D"
        done_mock.task_basis = "posting_date"
        done_mock.due_date = date(2026, 5, 1)
        done_mock.calculated_from = date(2026, 4, 29)
        done_mock.status = "Done"
        done_mock.created_at = "2026-04-19 00:00:00"
        done_mock.updated_at = "2026-04-19 00:00:00"
        done_mock.idoc_number = "IDOC001"

        with patch("app.routers.tasks.task_repo") as mock_repo, \
             patch("app.routers.tasks._assert_task_ownership"):
            mock_repo.get_by_id.return_value = task_mock
            mock_repo.mark_done.return_value = done_mock
            mock_repo.get_staff_name_for_task.return_value = "Benz"
            mock_repo.get_customer_name_for_task.return_value = "Somchai Jaidee"

            resp = client.patch(
                "/api/v1/tasks/1", json={"status": "Done"}, headers=bearer()
            )

        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert resp.json()["customer_name"] == "Somchai Jaidee"
        mock_repo.get_customer_name_for_task.assert_called_once()
        assert mock_repo.get_customer_name_for_task.call_args[0][1] == "IDOC001"
