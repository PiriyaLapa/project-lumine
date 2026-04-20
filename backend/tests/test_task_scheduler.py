"""
TDD — Task Scheduler tests.
Tests written BEFORE task_scheduler.py logic.
All test cases from SRS §5 FR-02 and §6.6.
"""
import pytest
from datetime import date
from unittest.mock import MagicMock, call

from app.services.task_scheduler import TaskScheduler, ScheduleResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_db():
    return MagicMock()


def make_transaction(
    idoc_number: str = "IDOC001",
    customer_id: str = "CUST001",
    posting_date: date = date(2026, 1, 10),
    staff_id: int = 1,
):
    t = MagicMock()
    t.idoc_number = idoc_number
    t.customer_id = customer_id
    t.posting_date = posting_date
    t.staff_id = staff_id
    return t


# ---------------------------------------------------------------------------
# Date calculation rules (SRS §5 FR-02)
# ---------------------------------------------------------------------------

class TestTaskDateCalculation:
    def test_t_plus_2_days_normal(self):
        """T+2: posting_date 2026-01-10 → due 2026-01-12."""
        result = TaskScheduler.calculate_due_dates(date(2026, 1, 10))
        assert result["2D"] == date(2026, 1, 12)

    def test_t_plus_14_days_normal(self):
        """T+14: posting_date 2026-01-10 → due 2026-01-24."""
        result = TaskScheduler.calculate_due_dates(date(2026, 1, 10))
        assert result["2W"] == date(2026, 1, 24)

    def test_t_plus_60_days_normal(self):
        """T+60: posting_date 2026-01-10 → due 2026-03-11."""
        result = TaskScheduler.calculate_due_dates(date(2026, 1, 10))
        assert result["2M"] == date(2026, 3, 11)

    def test_t_plus_60_leap_year_feb29(self):
        """T+60 crossing Feb 29 on a leap year must land on correct date."""
        # posting_date 2028-01-01 (2028 is a leap year) + 60 days = 2028-03-01
        result = TaskScheduler.calculate_due_dates(date(2028, 1, 1))
        assert result["2M"] == date(2028, 3, 1)

    def test_t_plus_60_non_leap_year_no_feb29(self):
        """T+60 in a non-leap year crossing Feb doesn't land on Feb 29."""
        # posting_date 2026-01-01 + 60 days = 2026-03-02 (no Feb 29 in 2026)
        result = TaskScheduler.calculate_due_dates(date(2026, 1, 1))
        assert result["2M"] == date(2026, 3, 2)

    def test_t_plus_60_month_boundary(self):
        """T+60 crossing a month boundary calculates correctly."""
        # posting_date 2026-11-30 + 60 days = 2027-01-29
        result = TaskScheduler.calculate_due_dates(date(2026, 11, 30))
        assert result["2M"] == date(2027, 1, 29)

    def test_t_plus_2_weekend_not_adjusted(self):
        """Weekend due dates are NOT adjusted — display as-is (SRS §5 FR-02)."""
        # 2026-01-09 is a Friday; +2 = 2026-01-11 (Sunday) — must NOT adjust
        result = TaskScheduler.calculate_due_dates(date(2026, 1, 9))
        assert result["2D"] == date(2026, 1, 11)  # Sunday, not adjusted

    def test_task_basis_is_always_posting_date(self):
        """task_basis field is always 'posting_date' (never call date or any other)."""
        result = TaskScheduler.calculate_due_dates(date(2026, 1, 10))
        assert result["task_basis"] == "posting_date"
        assert result["calculated_from"] == date(2026, 1, 10)


# ---------------------------------------------------------------------------
# Task creation (writes to DB via task_repo)
# ---------------------------------------------------------------------------

class TestTaskCreation:
    def test_creates_exactly_three_tasks(self):
        """One transaction → exactly 3 FollowUpTask records (2D, 2W, 2M)."""
        db = make_db()
        transaction = make_transaction()

        with MagicMock() as mock_repo:
            from unittest.mock import patch
            with patch("app.services.task_scheduler.task_repo") as mock_task_repo:
                mock_task_repo.create_tasks.return_value = None
                result = TaskScheduler.schedule(db, transaction)

        assert result.tasks_created == 3

    def test_task_types_are_2d_2w_2m(self):
        """The three created tasks have task_type values 2D, 2W, 2M."""
        from unittest.mock import patch
        db = make_db()
        transaction = make_transaction(posting_date=date(2026, 1, 10))

        with patch("app.services.task_scheduler.task_repo") as mock_task_repo:
            created_tasks = []
            mock_task_repo.create_tasks.side_effect = lambda db, tasks: created_tasks.extend(tasks)
            TaskScheduler.schedule(db, transaction)

        task_types = {t["task_type"] for t in created_tasks}
        assert task_types == {"2D", "2W", "2M"}

    def test_task_status_is_pending(self):
        """All newly created tasks have status=Pending."""
        from unittest.mock import patch
        db = make_db()
        transaction = make_transaction()

        with patch("app.services.task_scheduler.task_repo") as mock_task_repo:
            created_tasks = []
            mock_task_repo.create_tasks.side_effect = lambda db, tasks: created_tasks.extend(tasks)
            TaskScheduler.schedule(db, transaction)

        assert all(t["status"] == "Pending" for t in created_tasks)

    def test_task_customer_id_matches_transaction(self):
        """Tasks are linked to the correct customer_id."""
        from unittest.mock import patch
        db = make_db()
        transaction = make_transaction(customer_id="CUST999")

        with patch("app.services.task_scheduler.task_repo") as mock_task_repo:
            created_tasks = []
            mock_task_repo.create_tasks.side_effect = lambda db, tasks: created_tasks.extend(tasks)
            TaskScheduler.schedule(db, transaction)

        assert all(t["customer_id"] == "CUST999" for t in created_tasks)

    def test_task_idoc_number_matches_transaction(self):
        """Tasks reference the correct idoc_number."""
        from unittest.mock import patch
        db = make_db()
        transaction = make_transaction(idoc_number="IDOC_XYZ")

        with patch("app.services.task_scheduler.task_repo") as mock_task_repo:
            created_tasks = []
            mock_task_repo.create_tasks.side_effect = lambda db, tasks: created_tasks.extend(tasks)
            TaskScheduler.schedule(db, transaction)

        assert all(t["idoc_number"] == "IDOC_XYZ" for t in created_tasks)

    def test_due_dates_are_correct(self):
        """Due dates match posting_date + 2/14/60 days."""
        from unittest.mock import patch
        posting = date(2026, 3, 1)
        db = make_db()
        transaction = make_transaction(posting_date=posting)

        with patch("app.services.task_scheduler.task_repo") as mock_task_repo:
            created_tasks = []
            mock_task_repo.create_tasks.side_effect = lambda db, tasks: created_tasks.extend(tasks)
            TaskScheduler.schedule(db, transaction)

        by_type = {t["task_type"]: t for t in created_tasks}
        assert by_type["2D"]["due_date"] == date(2026, 3, 3)
        assert by_type["2W"]["due_date"] == date(2026, 3, 15)
        assert by_type["2M"]["due_date"] == date(2026, 4, 30)
