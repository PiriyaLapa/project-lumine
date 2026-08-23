"""
TDD — Multi-Staff Isolation tests.
SRS §5 FR-06 and §6.6.
Associate sees only own tasks; manager sees all under their store.
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.services.auth_service import AuthService
from app.models.follow_up_task import FollowUpTask
from datetime import date


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_token(staff_id: int, role: str, store_id: int) -> str:
    return AuthService.create_access_token({
        "staff_id": staff_id,
        "role": role,
        "store_id": store_id,
    })


def make_task(task_id: int, customer_id: str = "CUST001") -> FollowUpTask:
    t = MagicMock(spec=FollowUpTask)
    t.id = task_id
    t.customer_id = customer_id
    t.task_type = "2D"
    t.task_basis = "posting_date"
    t.due_date = date(2026, 5, 1)
    t.calculated_from = date(2026, 4, 29)
    t.status = "Pending"
    t.created_at = "2026-04-29T00:00:00"
    t.updated_at = "2026-04-29T00:00:00"
    return t


# ---------------------------------------------------------------------------
# Associate: own tasks only
# ---------------------------------------------------------------------------

class TestAssociateIsolation:
    def test_associate_gets_own_tasks(self):
        """GET /tasks for a sales_associate calls get_tasks_for_staff with their staff_id."""
        token = make_token(staff_id=10, role="sales_associate", store_id=1)
        tasks = [(make_task(1), "Benz", "Somchai Jaidee"), (make_task(2), "Benz", "Asia - Others")]

        with patch("app.routers.tasks.task_repo") as mock_repo:
            mock_repo.get_tasks_for_staff.return_value = tasks
            client = TestClient(app)
            resp = client.get(
                "/api/v1/tasks",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        mock_repo.get_tasks_for_staff.assert_called_once()
        call_args = mock_repo.get_tasks_for_staff.call_args
        assert call_args[0][1] == 10  # staff_id=10

    def test_associate_cannot_update_another_associates_task(self):
        """PATCH /tasks/{id} for a task owned by staff_id=99 raises 403 for staff_id=10."""
        token = make_token(staff_id=10, role="sales_associate", store_id=1)

        task = make_task(task_id=42)
        task.status = "Pending"
        task.idoc_number = "IDOC001"

        # Transaction owned by a different staff member
        other_transaction = MagicMock()
        other_transaction.staff_id = 99  # not staff_id=10

        def override_db():
            db = MagicMock()
            db.query.return_value.filter.return_value.first.side_effect = [
                task,           # task_repo.get_by_id
                other_transaction,  # _assert_task_ownership transaction lookup
            ]
            yield db

        app.dependency_overrides[get_db] = override_db
        client = TestClient(app)
        resp = client.patch(
            "/api/v1/tasks/42",
            json={"status": "Done"},
            headers={"Authorization": f"Bearer {token}"},
        )
        app.dependency_overrides.clear()

        assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Manager: all tasks in store
# ---------------------------------------------------------------------------

class TestManagerAccess:
    def test_manager_gets_all_store_tasks(self):
        """GET /tasks for a store_manager calls get_tasks_for_store with their store_id."""
        token = make_token(staff_id=1, role="store_manager", store_id=7)
        tasks = [
            (make_task(1), "Benz", "Somchai Jaidee"),
            (make_task(2), "Ann", "Asia - Others"),
            (make_task(3), "Benz", None),
        ]

        with patch("app.routers.tasks.task_repo") as mock_repo:
            mock_repo.get_tasks_for_store.return_value = tasks
            client = TestClient(app)
            resp = client.get(
                "/api/v1/tasks",
                headers={"Authorization": f"Bearer {token}"},
            )

        assert resp.status_code == 200
        mock_repo.get_tasks_for_store.assert_called_once()
        call_args = mock_repo.get_tasks_for_store.call_args
        assert call_args[0][1] == 7  # store_id=7

    def test_manager_can_update_any_task_in_store(self):
        """Manager can mark Done a task owned by any associate in their store."""
        token = make_token(staff_id=1, role="store_manager", store_id=7)

        task = make_task(task_id=55)
        task.status = "Pending"
        task.idoc_number = "IDOC_STORE"

        updated_task = make_task(task_id=55)
        updated_task.status = "Done"
        updated_task.idoc_number = "IDOC_STORE"

        def override_db():
            db = MagicMock()
            # get_by_id returns the task; mark_done returns updated task
            db.query.return_value.filter.return_value.first.return_value = task
            yield db

        app.dependency_overrides[get_db] = override_db

        with patch("app.routers.tasks.task_repo") as mock_repo:
            mock_repo.get_by_id.return_value = task
            mock_repo.mark_done.return_value = updated_task
            mock_repo.get_staff_name_for_task.return_value = "Benz"
            mock_repo.get_customer_name_for_task.return_value = "Somchai Jaidee"
            client = TestClient(app)
            resp = client.patch(
                "/api/v1/tasks/55",
                json={"status": "Done"},
                headers={"Authorization": f"Bearer {token}"},
            )

        app.dependency_overrides.clear()
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Status validation
# ---------------------------------------------------------------------------

class TestTaskStatusValidation:
    def test_only_done_status_accepted_via_patch(self):
        """PATCH with status='Superseded' returns 422."""
        token = make_token(staff_id=1, role="sales_associate", store_id=1)
        client = TestClient(app)
        resp = client.patch(
            "/api/v1/tasks/1",
            json={"status": "Superseded"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 422

    def test_patch_without_token_returns_403(self):
        client = TestClient(app)
        resp = client.patch("/api/v1/tasks/1", json={"status": "Done"})
        assert resp.status_code == 403
