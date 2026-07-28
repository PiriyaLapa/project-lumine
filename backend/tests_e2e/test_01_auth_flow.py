"""
E2E — login against the real DB, confirm the real JWT works on a protected
endpoint. Complements backend/tests/test_auth_router.py (mocked DB) by
proving the actual staff_repo/AuthService/middleware wiring works together
against a real MySQL instance.
"""
import httpx

from conftest import E2E_STAFF_EMAIL, E2E_STAFF_PASSWORD


class TestAuthFlow:
    def test_login_returns_real_token_pair(self, client: httpx.Client):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": E2E_STAFF_EMAIL, "password": E2E_STAFF_PASSWORD},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["access_token"]
        assert data["refresh_token"]
        assert data["role"] == "sales_associate"

    def test_wrong_password_returns_401(self, client: httpx.Client):
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": E2E_STAFF_EMAIL, "password": "wrong-password"},
        )
        assert resp.status_code == 401

    def test_real_token_authenticates_protected_endpoint(self, client: httpx.Client, auth_headers: dict):
        resp = client.get("/api/v1/tasks", headers=auth_headers)
        assert resp.status_code == 200

    def test_protected_endpoint_without_token_rejected(self, client: httpx.Client):
        resp = client.get("/api/v1/tasks")
        assert resp.status_code == 403
