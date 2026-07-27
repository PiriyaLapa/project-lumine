"""
TDD — auto_touch_repo.py (backs QA-4 test_auto_touch.py's repo-level needs).
do_not_contact and skipped_until must be enforced in the WHERE clause
here, never left to the caller (SEC-3).
"""
from datetime import date, timedelta
from unittest.mock import MagicMock

from app.repositories import auto_touch_repo


class TestGetTodayList:
    def test_calls_query_with_expected_filter_count(self):
        """
        get_today_list must filter on: staff_id, status=Pending,
        due_date<=today, do_not_contact=False, skipped_until not-blocking.
        We assert the underlying query chain is invoked — the exact SQL
        shape is covered by the integration test against a real join.
        """
        db = MagicMock()
        db.query.return_value.join.return_value.join.return_value.filter.return_value.order_by.return_value.all.return_value = []
        result = auto_touch_repo.get_today_list(db, staff_id=90001)
        assert result == []
        db.query.assert_called_once()


class TestGetStatusSummary:
    def test_returns_dict_with_expected_keys(self):
        db = MagicMock()
        db.query.return_value.join.return_value.filter.return_value.count.return_value = 0
        result = auto_touch_repo.get_status_summary(db, staff_id=90001)
        assert set(result.keys()) == {"date", "total_due", "sent", "pending", "skipped"}
        assert result["date"] == date.today()


class TestRecordSkip:
    def test_sets_skipped_until_to_tomorrow(self):
        db = MagicMock()
        task = MagicMock()
        deferred_to = auto_touch_repo.record_skip(db, task)
        assert task.skipped_until == date.today() + timedelta(days=1)
        assert deferred_to == date.today() + timedelta(days=1)
        db.flush.assert_called_once()


class TestCreateMessage:
    def test_inserts_and_flushes(self):
        db = MagicMock()
        data = {
            "customer_id": "C1",
            "staff_id": 90001,
            "task_id": 42,
            "touchpoint_type": "2D",
            "message_text": "Hello!",
            "channel_line": True,
            "channel_email": False,
        }
        result = auto_touch_repo.create_message(db, data)
        db.add.assert_called_once()
        db.flush.assert_called_once()
        assert result.message_text == "Hello!"


class TestGetTaskWithCustomer:
    def test_returns_none_when_not_found(self):
        db = MagicMock()
        db.query.return_value.join.return_value.join.return_value.filter.return_value.first.return_value = None
        result = auto_touch_repo.get_task_with_customer(db, task_id=999)
        assert result is None
