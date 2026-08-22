"""
E2E — mark a real task Done, log evidence for it, read it back. Runs after
test_02_upload_and_tasks_flow.py has created real tasks for E2E-CUST-001
(numeric filename prefixes control pytest's collection order).
"""
import httpx


class TestEvidenceFlow:
    def test_mark_done_then_log_and_read_evidence(self, client: httpx.Client, auth_headers: dict):
        tasks_resp = client.get("/api/v1/tasks", headers=auth_headers)
        assert tasks_resp.status_code == 200
        task = next(
            t for t in tasks_resp.json()
            if t["customer_id"] == "E2E-CUST-001" and t["task_type"] == "2D"
        )
        task_id = task["id"]

        patch_resp = client.patch(
            f"/api/v1/tasks/{task_id}", headers=auth_headers, json={"status": "Done"}
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["status"] == "Done"

        # No image — Drive upload is intentionally not exercised here; a
        # missing/invalid credentials.json fails non-fatally (image_uri=null).
        evidence_resp = client.post(
            "/api/v1/evidence",
            headers=auth_headers,
            data={"task_id": str(task_id), "notes": "E2E: called customer, confirmed happy with purchase."},
        )
        assert evidence_resp.status_code == 200, evidence_resp.text
        evidence = evidence_resp.json()
        assert evidence["task_id"] == task_id
        assert evidence["notes"] == "E2E: called customer, confirmed happy with purchase."

        get_resp = client.get(f"/api/v1/evidence/{task_id}", headers=auth_headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["id"] == evidence["id"]

    def test_evidence_for_unknown_task_returns_404(self, client: httpx.Client, auth_headers: dict):
        resp = client.get("/api/v1/evidence/999999", headers=auth_headers)
        assert resp.status_code == 404
