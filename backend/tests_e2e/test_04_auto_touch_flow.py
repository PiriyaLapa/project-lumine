"""
E2E — GET /api/v1/auto-touch/today and /status against the real data left
by test_02 (2D marked Done in test_03; 2W/2M still Pending).

Note: /today inner-joins Customer (do_not_contact enforcement), and the
E2E fixture is a SAP-only upload with no `customers` row — by design (SAP-only
customers are a real, common case per migration 0006's docstring), so it
correctly never appears in /today. /status's `pending` count does not join
Customer, so it does pick up the real Pending 2W/2M tasks.
"""
import httpx


class TestAutoTouchFlow:
    def test_today_list_responds_with_correct_shape(self, client: httpx.Client, auth_headers: dict):
        resp = client.get("/api/v1/auto-touch/today", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_status_counts_real_pending_tasks(self, client: httpx.Client, auth_headers: dict):
        resp = client.get("/api/v1/auto-touch/status", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        # 2D was marked Done in test_03; 2W (overdue) and 2M remain Pending.
        assert data["pending"] >= 1

    def test_requires_jwt(self, client: httpx.Client):
        resp = client.get("/api/v1/auto-touch/today")
        assert resp.status_code == 403
