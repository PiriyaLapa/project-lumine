"""
TDD — Cycle Reset tests.
Tests written BEFORE cycle_reset.py logic.
All test cases from SRS §5 FR-03 and §6.6.
"""
import pytest
from datetime import date
from unittest.mock import MagicMock, patch, call

from app.services.cycle_reset import CycleReset, ResetResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_pending_task(task_id: int, customer_id: str = "CUST001"):
    t = MagicMock()
    t.id = task_id
    t.customer_id = customer_id
    t.status = "Pending"
    return t


def make_transaction(
    idoc_number: str = "IDOC_NEW",
    customer_id: str = "CUST001",
    posting_date: date = date(2026, 6, 1),
    staff_id: int = 1,
):
    t = MagicMock()
    t.idoc_number = idoc_number
    t.customer_id = customer_id
    t.posting_date = posting_date
    t.staff_id = staff_id
    return t


# ---------------------------------------------------------------------------
# SRS §5 FR-03: 3 cases
# ---------------------------------------------------------------------------

class TestCycleReset:
    def test_no_pending_tasks_first_purchase(self):
        """
        First purchase for a customer — 0 pending tasks.
        No tasks superseded. Fresh 2-2-2 created. cycles_reset=0.
        """
        db = MagicMock()
        transaction = make_transaction()

        with patch("app.services.cycle_reset.task_repo") as mock_task_repo, \
             patch("app.services.cycle_reset.TaskScheduler") as mock_sched:
            mock_task_repo.get_pending_by_customer.return_value = []
            mock_sched.schedule.return_value = MagicMock(tasks_created=3)

            result = CycleReset.run(db, transaction)

        assert result.tasks_superseded == 0
        assert result.cycles_reset == 0
        mock_task_repo.supersede_tasks.assert_not_called()
        mock_sched.schedule.assert_called_once_with(db, transaction)

    def test_one_pending_task_superseded(self):
        """
        Customer has 1 pending task from a prior purchase.
        That task is superseded, fresh 2-2-2 is created. cycles_reset=1.
        """
        db = MagicMock()
        transaction = make_transaction()
        pending = [make_pending_task(task_id=10)]

        with patch("app.services.cycle_reset.task_repo") as mock_task_repo, \
             patch("app.services.cycle_reset.TaskScheduler") as mock_sched:
            mock_task_repo.get_pending_by_customer.return_value = pending
            mock_task_repo.supersede_tasks.return_value = 1
            mock_sched.schedule.return_value = MagicMock(tasks_created=3)

            result = CycleReset.run(db, transaction)

        assert result.tasks_superseded == 1
        assert result.cycles_reset == 1
        mock_task_repo.supersede_tasks.assert_called_once_with(db, [10])
        mock_sched.schedule.assert_called_once_with(db, transaction)

    def test_three_pending_tasks_all_superseded(self):
        """
        Customer has all 3 pending tasks (full active cycle).
        All 3 superseded, fresh 2-2-2 created. cycles_reset=1.
        """
        db = MagicMock()
        transaction = make_transaction()
        pending = [
            make_pending_task(task_id=1),
            make_pending_task(task_id=2),
            make_pending_task(task_id=3),
        ]

        with patch("app.services.cycle_reset.task_repo") as mock_task_repo, \
             patch("app.services.cycle_reset.TaskScheduler") as mock_sched:
            mock_task_repo.get_pending_by_customer.return_value = pending
            mock_task_repo.supersede_tasks.return_value = 3
            mock_sched.schedule.return_value = MagicMock(tasks_created=3)

            result = CycleReset.run(db, transaction)

        assert result.tasks_superseded == 3
        assert result.cycles_reset == 1
        mock_task_repo.supersede_tasks.assert_called_once_with(db, [1, 2, 3])

    def test_supersede_before_create(self):
        """
        Old tasks must be superseded BEFORE new tasks are created.
        Ensures no brief period where both old and new tasks are Pending.
        """
        db = MagicMock()
        transaction = make_transaction()
        pending = [make_pending_task(task_id=5)]
        call_order = []

        with patch("app.services.cycle_reset.task_repo") as mock_task_repo, \
             patch("app.services.cycle_reset.TaskScheduler") as mock_sched:
            mock_task_repo.get_pending_by_customer.return_value = pending
            mock_task_repo.supersede_tasks.side_effect = lambda db, ids: call_order.append("supersede")
            mock_sched.schedule.side_effect = lambda db, t: (call_order.append("schedule"), MagicMock(tasks_created=3))[1]

            CycleReset.run(db, transaction)

        assert call_order == ["supersede", "schedule"]

    def test_only_pending_tasks_superseded_not_done(self):
        """
        Done tasks are NOT superseded — only Pending tasks are affected.
        get_pending_by_customer must filter by status=Pending.
        """
        db = MagicMock()
        transaction = make_transaction()

        with patch("app.services.cycle_reset.task_repo") as mock_task_repo, \
             patch("app.services.cycle_reset.TaskScheduler") as mock_sched:
            mock_task_repo.get_pending_by_customer.return_value = []
            mock_sched.schedule.return_value = MagicMock(tasks_created=3)
            CycleReset.run(db, transaction)

        # Verify query is for this customer's pending tasks
        mock_task_repo.get_pending_by_customer.assert_called_once_with(
            db, transaction.customer_id
        )

    def test_result_contains_tasks_created(self):
        """ResetResult reports how many new tasks were created."""
        db = MagicMock()
        transaction = make_transaction()

        with patch("app.services.cycle_reset.task_repo") as mock_task_repo, \
             patch("app.services.cycle_reset.TaskScheduler") as mock_sched:
            mock_task_repo.get_pending_by_customer.return_value = []
            mock_sched.schedule.return_value = MagicMock(tasks_created=3)

            result = CycleReset.run(db, transaction)

        assert result.tasks_created == 3
