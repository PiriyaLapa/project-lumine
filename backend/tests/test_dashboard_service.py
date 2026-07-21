"""
TDD — dashboard_service.py. Tests written before the logic.
Follow-Up Dashboard: sales_associate sees their own single-row stats;
store_manager sees a per-staff breakdown across the store — same
StaffFollowUpStats shape and _stats_for_staff calculation for both.
"""
from datetime import date, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.services.dashboard_service import DashboardService, resolve_period_range


def make_db():
    return MagicMock()


def make_staff(staff_id, name="Test Staff"):
    s = MagicMock()
    s.id = staff_id
    s.name = name
    return s


def make_task(status="Pending", skipped_until=None):
    t = MagicMock()
    t.status = status
    t.skipped_until = skipped_until
    return t


def make_message(staff_id, customer_id, status_line=None, status_email=None):
    m = MagicMock()
    m.staff_id = staff_id
    m.customer_id = customer_id
    m.status_line = status_line
    m.status_email = status_email
    return m


# ---------------------------------------------------------------------------
# resolve_period_range — pure function, no mocking
# ---------------------------------------------------------------------------

class TestResolvePeriodRange:
    def test_today_returns_today_both_ends(self):
        today = date(2026, 7, 21)
        assert resolve_period_range("today", today) == (today, today)

    def test_week_returns_monday_to_today_midweek(self):
        today = date(2026, 7, 21)  # Tuesday
        date_from, date_to = resolve_period_range("week", today)
        assert date_from == date(2026, 7, 20)  # Monday
        assert date_to == today

    def test_week_when_today_is_monday(self):
        today = date(2026, 7, 20)  # Monday
        date_from, date_to = resolve_period_range("week", today)
        assert date_from == today
        assert date_to == today

    def test_month_returns_first_of_month_to_today(self):
        today = date(2026, 7, 21)
        date_from, date_to = resolve_period_range("month", today)
        assert date_from == date(2026, 7, 1)
        assert date_to == today

    def test_all_returns_none_none(self):
        assert resolve_period_range("all", date.today()) == (None, None)

    def test_unknown_period_raises_value_error(self):
        with pytest.raises(ValueError):
            resolve_period_range("year", date.today())


# ---------------------------------------------------------------------------
# get_manager_dashboard
# ---------------------------------------------------------------------------

class TestGetManagerDashboard:
    def test_zero_staff_zero_everything(self):
        db = make_db()
        with patch("app.services.dashboard_service.dashboard_repo") as mock_repo:
            mock_repo.get_active_staff_for_store.return_value = []
            mock_repo.get_tasks_for_store_dashboard.return_value = []
            mock_repo.get_messages_for_store_dashboard.return_value = []
            result = DashboardService.get_manager_dashboard(db, store_id=8902, period="today")

        assert result.staff_breakdown == []
        assert result.store_totals.tasks_due == 0
        assert result.store_totals.customers_followed_up == 0

    def test_staff_with_zero_tasks_appears_as_zero_row(self):
        db = make_db()
        with patch("app.services.dashboard_service.dashboard_repo") as mock_repo:
            mock_repo.get_active_staff_for_store.return_value = [make_staff(90001, "Jane")]
            mock_repo.get_tasks_for_store_dashboard.return_value = []
            mock_repo.get_messages_for_store_dashboard.return_value = []
            result = DashboardService.get_manager_dashboard(db, store_id=8902, period="today")

        assert len(result.staff_breakdown) == 1
        row = result.staff_breakdown[0]
        assert row.staff_id == 90001
        assert row.staff_name == "Jane"
        assert row.tasks_due == 0

    def test_mixed_staff_correct_per_staff_isolation(self):
        db = make_db()
        tasks = [
            (make_task("Done"), 90001),
            (make_task("Pending"), 90001),
            (make_task("Done"), 90002),
        ]
        with patch("app.services.dashboard_service.dashboard_repo") as mock_repo:
            mock_repo.get_active_staff_for_store.return_value = [
                make_staff(90001, "Jane"), make_staff(90002, "John"),
            ]
            mock_repo.get_tasks_for_store_dashboard.return_value = tasks
            mock_repo.get_messages_for_store_dashboard.return_value = []
            result = DashboardService.get_manager_dashboard(db, store_id=8902, period="today")

        jane, john = result.staff_breakdown
        assert jane.tasks_due == 2
        assert jane.tasks_done == 1
        assert john.tasks_due == 1
        assert john.tasks_done == 1

    def test_all_tasks_skipped(self):
        db = make_db()
        tasks = [(make_task("Pending", skipped_until=date.today() + timedelta(days=1)), 90001)]
        with patch("app.services.dashboard_service.dashboard_repo") as mock_repo:
            mock_repo.get_active_staff_for_store.return_value = [make_staff(90001)]
            mock_repo.get_tasks_for_store_dashboard.return_value = tasks
            mock_repo.get_messages_for_store_dashboard.return_value = []
            result = DashboardService.get_manager_dashboard(db, store_id=8902, period="today")

        row = result.staff_breakdown[0]
        assert row.tasks_skipped == 1
        assert row.tasks_done == 0

    def test_all_tasks_done(self):
        db = make_db()
        tasks = [(make_task("Done"), 90001), (make_task("Done"), 90001)]
        with patch("app.services.dashboard_service.dashboard_repo") as mock_repo:
            mock_repo.get_active_staff_for_store.return_value = [make_staff(90001)]
            mock_repo.get_tasks_for_store_dashboard.return_value = tasks
            mock_repo.get_messages_for_store_dashboard.return_value = []
            result = DashboardService.get_manager_dashboard(db, store_id=8902, period="today")

        row = result.staff_breakdown[0]
        assert row.tasks_pending == 0
        assert row.tasks_done == 2

    def test_channel_split_line_vs_email(self):
        db = make_db()
        messages = [
            make_message(90001, "C1", status_line="sent"),
            make_message(90001, "C2", status_email="sent"),
        ]
        with patch("app.services.dashboard_service.dashboard_repo") as mock_repo:
            mock_repo.get_active_staff_for_store.return_value = [make_staff(90001)]
            mock_repo.get_tasks_for_store_dashboard.return_value = []
            mock_repo.get_messages_for_store_dashboard.return_value = messages
            result = DashboardService.get_manager_dashboard(db, store_id=8902, period="today")

        row = result.staff_breakdown[0]
        assert row.messages_sent_line == 1
        assert row.messages_sent_email == 1

    def test_customers_followed_up_deduplicates_same_customer(self):
        db = make_db()
        messages = [
            make_message(90001, "C1", status_line="sent"),
            make_message(90001, "C1", status_email="sent"),
        ]
        with patch("app.services.dashboard_service.dashboard_repo") as mock_repo:
            mock_repo.get_active_staff_for_store.return_value = [make_staff(90001)]
            mock_repo.get_tasks_for_store_dashboard.return_value = []
            mock_repo.get_messages_for_store_dashboard.return_value = messages
            result = DashboardService.get_manager_dashboard(db, store_id=8902, period="today")

        assert result.staff_breakdown[0].customers_followed_up == 1

    def test_failed_message_not_counted_as_sent(self):
        db = make_db()
        messages = [make_message(90001, "C1", status_line="failed")]
        with patch("app.services.dashboard_service.dashboard_repo") as mock_repo:
            mock_repo.get_active_staff_for_store.return_value = [make_staff(90001)]
            mock_repo.get_tasks_for_store_dashboard.return_value = []
            mock_repo.get_messages_for_store_dashboard.return_value = messages
            result = DashboardService.get_manager_dashboard(db, store_id=8902, period="today")

        row = result.staff_breakdown[0]
        assert row.messages_sent_line == 0
        assert row.customers_followed_up == 0

    def test_store_totals_sums_all_staff_rows(self):
        db = make_db()
        tasks = [(make_task("Done"), 90001), (make_task("Done"), 90002)]
        with patch("app.services.dashboard_service.dashboard_repo") as mock_repo:
            mock_repo.get_active_staff_for_store.return_value = [
                make_staff(90001), make_staff(90002),
            ]
            mock_repo.get_tasks_for_store_dashboard.return_value = tasks
            mock_repo.get_messages_for_store_dashboard.return_value = []
            result = DashboardService.get_manager_dashboard(db, store_id=8902, period="today")

        assert result.store_totals.tasks_due == 2
        assert result.store_totals.tasks_done == 2
        assert result.store_totals.staff_id is None
        assert result.store_totals.staff_name is None

    def test_period_all_passes_none_none_to_repo(self):
        db = make_db()
        with patch("app.services.dashboard_service.dashboard_repo") as mock_repo:
            mock_repo.get_active_staff_for_store.return_value = []
            mock_repo.get_tasks_for_store_dashboard.return_value = []
            mock_repo.get_messages_for_store_dashboard.return_value = []
            DashboardService.get_manager_dashboard(db, store_id=8902, period="all")

        mock_repo.get_tasks_for_store_dashboard.assert_called_once_with(db, 8902, None, None)
        mock_repo.get_messages_for_store_dashboard.assert_called_once_with(db, 8902, None, None)


# ---------------------------------------------------------------------------
# get_staff_dashboard
# ---------------------------------------------------------------------------

class TestGetStaffDashboard:
    def test_single_row_output_matches_own_totals(self):
        db = make_db()
        tasks = [(make_task("Done"), 90001)]
        with patch("app.services.dashboard_service.staff_repo") as mock_staff_repo, \
             patch("app.services.dashboard_service.dashboard_repo") as mock_repo:
            mock_staff_repo.get_by_id.return_value = make_staff(90001, "Jane")
            mock_repo.get_tasks_for_staff_dashboard.return_value = tasks
            mock_repo.get_messages_for_staff_dashboard.return_value = []
            result = DashboardService.get_staff_dashboard(
                db, staff_id=90001, store_id=8902, period="today"
            )

        assert len(result.staff_breakdown) == 1
        assert result.staff_breakdown[0] is result.store_totals
        assert result.staff_breakdown[0].staff_id == 90001
        assert result.staff_breakdown[0].staff_name == "Jane"
        assert result.staff_breakdown[0].tasks_due == 1
        assert result.store_id == 8902

    def test_scoped_to_own_staff_id_only(self):
        db = make_db()
        with patch("app.services.dashboard_service.staff_repo") as mock_staff_repo, \
             patch("app.services.dashboard_service.dashboard_repo") as mock_repo:
            mock_staff_repo.get_by_id.return_value = make_staff(90001, "Jane")
            mock_repo.get_tasks_for_staff_dashboard.return_value = []
            mock_repo.get_messages_for_staff_dashboard.return_value = []
            DashboardService.get_staff_dashboard(db, staff_id=90001, store_id=8902, period="week")

        mock_repo.get_tasks_for_staff_dashboard.assert_called_once()
        assert mock_repo.get_tasks_for_staff_dashboard.call_args[0][1] == 90001
        mock_repo.get_active_staff_for_store.assert_not_called()
