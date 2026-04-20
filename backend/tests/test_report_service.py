"""
TDD — Report Service tests.
Tests written BEFORE report_service.py logic.
SRS §5 FR-06, §6.6 KPI: completion_rate = Done / (Pending + Done); Superseded excluded.
"""
import pytest
from unittest.mock import MagicMock, patch

from app.services.report_service import ReportService, KPIResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_db():
    return MagicMock()


def make_task(status: str):
    t = MagicMock()
    t.status = status
    return t


# ---------------------------------------------------------------------------
# KPI calculation (SRS §6.6)
# ---------------------------------------------------------------------------

class TestKPICalculation:
    def test_completion_rate_all_done(self):
        """3 Done tasks → completion_rate = 1.0"""
        db = make_db()
        tasks = [make_task("Done"), make_task("Done"), make_task("Done")]

        with patch("app.services.report_service.kpi_repo") as mock_repo:
            mock_repo.get_tasks_for_staff_kpi.return_value = tasks

            result = ReportService.get_kpi_for_staff(db=db, staff_id=1, store_id=10)

        assert result.total_tasks == 3
        assert result.completed_tasks == 3
        assert result.completion_rate == pytest.approx(1.0)

    def test_completion_rate_mixed(self):
        """2 Done + 1 Pending → completion_rate = 0.667"""
        db = make_db()
        tasks = [make_task("Done"), make_task("Done"), make_task("Pending")]

        with patch("app.services.report_service.kpi_repo") as mock_repo:
            mock_repo.get_tasks_for_staff_kpi.return_value = tasks

            result = ReportService.get_kpi_for_staff(db=db, staff_id=1, store_id=10)

        assert result.total_tasks == 3
        assert result.completed_tasks == 2
        assert result.completion_rate == pytest.approx(2 / 3)

    def test_superseded_tasks_excluded(self):
        """
        Superseded tasks do NOT count in total_tasks or completed_tasks.
        SRS: 'Superseded → archived, excluded from KPI score'
        """
        db = make_db()
        tasks = [make_task("Done"), make_task("Superseded"), make_task("Superseded")]

        with patch("app.services.report_service.kpi_repo") as mock_repo:
            mock_repo.get_tasks_for_staff_kpi.return_value = tasks

            result = ReportService.get_kpi_for_staff(db=db, staff_id=1, store_id=10)

        assert result.total_tasks == 1      # only Done counts
        assert result.completed_tasks == 1
        assert result.completion_rate == pytest.approx(1.0)

    def test_no_tasks_returns_zero_rate(self):
        """No tasks → completion_rate = 0.0, not a division-by-zero error."""
        db = make_db()

        with patch("app.services.report_service.kpi_repo") as mock_repo:
            mock_repo.get_tasks_for_staff_kpi.return_value = []

            result = ReportService.get_kpi_for_staff(db=db, staff_id=1, store_id=10)

        assert result.total_tasks == 0
        assert result.completed_tasks == 0
        assert result.completion_rate == 0.0

    def test_only_pending_tasks(self):
        """All Pending → completed = 0, total = count, rate = 0.0."""
        db = make_db()
        tasks = [make_task("Pending"), make_task("Pending")]

        with patch("app.services.report_service.kpi_repo") as mock_repo:
            mock_repo.get_tasks_for_staff_kpi.return_value = tasks

            result = ReportService.get_kpi_for_staff(db=db, staff_id=1, store_id=10)

        assert result.total_tasks == 2
        assert result.completed_tasks == 0
        assert result.completion_rate == 0.0


# ---------------------------------------------------------------------------
# Multi-staff isolation (SRS §5 FR-06)
# ---------------------------------------------------------------------------

class TestKPIIsolation:
    def test_staff_kpi_uses_staff_id(self):
        """Sales associate KPI queries by staff_id (own tasks only)."""
        db = make_db()

        with patch("app.services.report_service.kpi_repo") as mock_repo:
            mock_repo.get_tasks_for_staff_kpi.return_value = []

            ReportService.get_kpi_for_staff(db=db, staff_id=42, store_id=5)

        mock_repo.get_tasks_for_staff_kpi.assert_called_once_with(db, staff_id=42)
        mock_repo.get_tasks_for_store_kpi.assert_not_called()

    def test_manager_kpi_uses_store_id(self):
        """Store manager KPI queries by store_id (all staff in store)."""
        db = make_db()

        with patch("app.services.report_service.kpi_repo") as mock_repo:
            mock_repo.get_tasks_for_store_kpi.return_value = []

            ReportService.get_kpi_for_store(db=db, store_id=5)

        mock_repo.get_tasks_for_store_kpi.assert_called_once_with(db, store_id=5)
        mock_repo.get_tasks_for_staff_kpi.assert_not_called()

    def test_store_kpi_result_has_store_id(self):
        """Store-level KPIResult includes store_id, staff_id=None."""
        db = make_db()

        with patch("app.services.report_service.kpi_repo") as mock_repo:
            mock_repo.get_tasks_for_store_kpi.return_value = [make_task("Done")]

            result = ReportService.get_kpi_for_store(db=db, store_id=7)

        assert result.store_id == 7
        assert result.staff_id is None

    def test_staff_kpi_result_has_staff_id(self):
        """Staff-level KPIResult includes staff_id and store_id."""
        db = make_db()

        with patch("app.services.report_service.kpi_repo") as mock_repo:
            mock_repo.get_tasks_for_staff_kpi.return_value = []

            result = ReportService.get_kpi_for_staff(db=db, staff_id=9, store_id=3)

        assert result.staff_id == 9
        assert result.store_id == 3
