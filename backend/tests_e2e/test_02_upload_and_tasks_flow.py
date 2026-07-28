"""
E2E — upload a real SAP export through the real parser/repo/CycleReset
chain, confirm real FollowUpTask rows come back with correct 2-2-2 due-date
math. Assumes a freshly wiped+seeded E2E stack (docker-compose.e2e.yml
down -v && up -d, then seed) — re-uploading the same fixture into a
non-empty DB will hit the real duplicate-date-range 409, which is correct
behavior, not something this test works around.
"""
from datetime import date
from pathlib import Path

import httpx

FIXTURE = Path(__file__).parent / "fixtures" / "sap_export_e2e.csv"

# fixtures/sap_export_e2e.csv posting_date is fixed at 2026-06-01
POSTING_DATE = date(2026, 6, 1)
EXPECTED_DUE_DATES = {
    "2D": date(2026, 6, 3),
    "2W": date(2026, 6, 15),
    "2M": date(2026, 7, 31),
}


class TestUploadAndTasksFlow:
    def test_upload_creates_three_tasks_with_correct_due_dates(self, client: httpx.Client, auth_headers: dict):
        with open(FIXTURE, "rb") as f:
            resp = client.post(
                "/api/v1/upload",
                headers=auth_headers,
                files={"file": ("sap_export_e2e.csv", f, "text/csv")},
            )
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert body["tasks_created"] == 3
        assert body["customers_processed"] == 1

        tasks_resp = client.get("/api/v1/tasks", headers=auth_headers)
        assert tasks_resp.status_code == 200
        tasks = [t for t in tasks_resp.json() if t["customer_id"] == "E2E-CUST-001"]
        assert len(tasks) == 3

        by_type = {t["task_type"]: t for t in tasks}
        assert set(by_type.keys()) == {"2D", "2W", "2M"}
        for task_type, expected_due in EXPECTED_DUE_DATES.items():
            assert by_type[task_type]["due_date"] == expected_due.isoformat()
            assert by_type[task_type]["status"] == "Pending"
            assert by_type[task_type]["task_basis"] == "posting_date"

    def test_reuploading_same_date_range_conflicts(self, client: httpx.Client, auth_headers: dict):
        with open(FIXTURE, "rb") as f:
            resp = client.post(
                "/api/v1/upload",
                headers=auth_headers,
                files={"file": ("sap_export_e2e.csv", f, "text/csv")},
            )
        assert resp.status_code == 409
        assert resp.json()["conflict"] is True
