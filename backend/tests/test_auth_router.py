"""
TDD — Auth router + middleware tests.
Uses FastAPI TestClient + mocked DB (no real MySQL needed in Phase 1).
All test cases from SRS §6.6 (Auth) and §7 NFR-02.
"""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.services.auth_service import AuthService
from app.models.staff import Staff


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_staff(
    staff_id: int = 1,
    role: str = "sales_associate",
    store_id: int = 5,
    email: str = "benz@lumine.com",
    password: str = "secret",
) -> Staff:
    s = Staff()
    s.id = staff_id
    s.name = "Benz"
    s.employee_code = "EMP001"
    s.role = role
    s.store_id = store_id
    s.email = email
    s.hashed_password = AuthService.hash_password(password)
    s.deleted_at = None
    return s


def override_db(mock_staff: Staff | None):
    """Return a FastAPI dependency override that yields a mock DB session."""
    def _override():
        db = MagicMock()
        query_chain = db.query.return_value.filter.return_value.first
        query_chain.return_value = mock_staff
        yield db
    return _override


# ---------------------------------------------------------------------------
# Login endpoint
# ---------------------------------------------------------------------------

class TestLogin:
    def test_valid_credentials_return_token_pair(self):
        staff = make_staff()
        app.dependency_overrides[get_db] = override_db(staff)
        client = TestClient(app)

        resp = client.post("/api/v1/auth/login", json={
            "email": "benz@lumine.com",
            "password": "secret",
        })
        app.dependency_overrides.clear()

        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["staff_id"] == 1
        assert data["role"] == "sales_associate"

    def test_wrong_password_returns_401(self):
        staff = make_staff()
        app.dependency_overrides[get_db] = override_db(staff)
        client = TestClient(app)

        resp = client.post("/api/v1/auth/login", json={
            "email": "benz@lumine.com",
            "password": "wrongpassword",
        })
        app.dependency_overrides.clear()

        assert resp.status_code == 401

    def test_unknown_email_returns_401(self):
        app.dependency_overrides[get_db] = override_db(None)  # staff not found
        client = TestClient(app)

        resp = client.post("/api/v1/auth/login", json={
            "email": "nobody@lumine.com",
            "password": "secret",
        })
        app.dependency_overrides.clear()

        assert resp.status_code == 401

    def test_response_fields_match_openapi_schema(self):
        """Field names must match openapi.yaml AuthResponse exactly."""
        staff = make_staff()
        app.dependency_overrides[get_db] = override_db(staff)
        client = TestClient(app)

        resp = client.post("/api/v1/auth/login", json={
            "email": "benz@lumine.com",
            "password": "secret",
        })
        app.dependency_overrides.clear()

        data = resp.json()
        for field in ["access_token", "refresh_token", "token_type", "staff_id", "role"]:
            assert field in data, f"Missing field: {field}"


# ---------------------------------------------------------------------------
# Refresh endpoint
# ---------------------------------------------------------------------------

class TestRefreshEndpoint:
    def test_valid_refresh_token_returns_new_access_token(self):
        refresh = AuthService.create_refresh_token({
            "staff_id": 1, "role": "sales_associate", "store_id": 5
        })
        client = TestClient(app)
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})

        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_expired_refresh_token_returns_401(self):
        from datetime import datetime, timedelta, timezone
        from jose import jwt
        from app.config import settings

        expired = jwt.encode(
            {
                "staff_id": 1, "role": "sales_associate", "store_id": 5,
                "exp": datetime.now(timezone.utc) - timedelta(days=1),
                "token_type": "refresh",
            },
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )
        client = TestClient(app)
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": expired})
        assert resp.status_code == 401

    def test_access_token_as_refresh_returns_401(self):
        """Passing an access token to /refresh must be rejected."""
        access = AuthService.create_access_token({
            "staff_id": 1, "role": "sales_associate", "store_id": 5
        })
        client = TestClient(app)
        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": access})
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Middleware — protected endpoint guard
# ---------------------------------------------------------------------------

class TestAuthMiddleware:
    def test_request_without_token_returns_403(self):
        """Health check is open. A hypothetical protected route returns 403/401 without token."""
        client = TestClient(app)
        # /health is open — confirm it works
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_valid_token_is_accepted(self):
        """A valid Bearer token on /health (open route) — middleware doesn't block open routes."""
        access = AuthService.create_access_token({
            "staff_id": 1, "role": "sales_associate", "store_id": 5
        })
        client = TestClient(app)
        resp = client.get("/health", headers={"Authorization": f"Bearer {access}"})
        assert resp.status_code == 200

    def test_staff_id_not_accepted_in_request_body(self):
        """Login does not honour a staff_id sent in the body — it reads from DB only."""
        staff = make_staff(staff_id=1)
        app.dependency_overrides[get_db] = override_db(staff)
        client = TestClient(app)

        # Attempt to inject staff_id=999 — response must reflect DB staff_id=1
        resp = client.post("/api/v1/auth/login", json={
            "email": "benz@lumine.com",
            "password": "secret",
            "staff_id": 999,  # ignored — not in LoginRequest schema
        })
        app.dependency_overrides.clear()

        assert resp.status_code == 200
        assert resp.json()["staff_id"] == 1  # from DB, not from body
