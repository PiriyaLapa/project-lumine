"""
TDD — dashboard_repo.py. Follow-Up Dashboard queries: store-wide (manager)
and staff-scoped (associate) variants for tasks and messages, plus the
active-staff roster used to build the manager's per-staff breakdown.
We assert the underlying query chain is invoked — the exact SQL shape is
covered by the integration test against a real join (same convention as
test_auto_touch_repo.py).
"""
from datetime import date, timedelta
from unittest.mock import MagicMock

from app.repositories import dashboard_repo


class TestGetActiveStaffForStore:
    def test_returns_query_result(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        result = dashboard_repo.get_active_staff_for_store(db, store_id=8902)
        assert result == []
        db.query.assert_called_once()


class TestGetTasksForStoreDashboard:
    def test_calls_query_with_date_range(self):
        db = MagicMock()
        db.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = []
        result = dashboard_repo.get_tasks_for_store_dashboard(
            db, store_id=8902, date_from=date.today(), date_to=date.today()
        )
        assert result == []
        db.query.assert_called_once()

    def test_period_all_unbounded_does_not_crash(self):
        db = MagicMock()
        db.query.return_value.join.return_value.join.return_value.filter.return_value.all.return_value = []
        result = dashboard_repo.get_tasks_for_store_dashboard(
            db, store_id=8902, date_from=None, date_to=None
        )
        assert result == []


class TestGetMessagesForStoreDashboard:
    def test_calls_query_with_date_range(self):
        db = MagicMock()
        db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        result = dashboard_repo.get_messages_for_store_dashboard(
            db, store_id=8902, date_from=date.today() - timedelta(days=7), date_to=date.today()
        )
        assert result == []
        db.query.assert_called_once()


class TestGetTasksForStaffDashboard:
    def test_calls_query_with_date_range(self):
        db = MagicMock()
        db.query.return_value.join.return_value.filter.return_value.all.return_value = []
        result = dashboard_repo.get_tasks_for_staff_dashboard(
            db, staff_id=90001, date_from=date.today(), date_to=date.today()
        )
        assert result == []
        db.query.assert_called_once()


class TestGetMessagesForStaffDashboard:
    def test_calls_query_with_date_range(self):
        db = MagicMock()
        db.query.return_value.filter.return_value.all.return_value = []
        result = dashboard_repo.get_messages_for_staff_dashboard(
            db, staff_id=90001, date_from=date.today(), date_to=date.today()
        )
        assert result == []
        db.query.assert_called_once()
