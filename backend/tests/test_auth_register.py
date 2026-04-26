"""
TDD — POST /api/v1/auth/register endpoint.
Tests written before implementation per CLAUDE.md TDD rule.
Covers all 6 cases from the approved spec.
"""
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.services.auth_service import AuthService
from app.models.staff import Staff


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_staff(staff_id: int = 10, role: str = "sales_associate", store_id: int = 1) -> Staff:
    s = Staff()
    s.id = staff_id
    s.name = "Test User"
    s.employee_code = "REG-test-uuid"
    s.role = role
    s.store_id = store_id
    s.email = "test@lumine.com"
    s.hashed_password = AuthService.hash_password("password123")
    s.deleted_at = None
    return s


def db_override():
    def _inner():
        yield MagicMock()
    return _inner


VALID = {
    "full_name": "Test User",
    "email": "test@lumine.com",
    "password": "password123",
    "confirm_password": "password123",
    "role": "sales_associate",
    "store_id": 1,
}


# ---------------------------------------------------------------------------
# Register endpoint
# ---------------------------------------------------------------------------

class TestRegister:

    def test_happy_path_returns_201_and_tokens(self):
        new_staff = make_staff()
        app.dependency_overrides[get_db] = db_override()
        client = TestClient(app)

        with patch("app.routers.auth.staff_repo.get_by_email", return_value=None), \
             patch("app.routers.auth.staff_repo.create_staff", return_value=new_staff):
            resp = client.post("/api/v1/auth/register", json=VALID)

        app.dependency_overrides.clear()

        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["staff_id"] == 10
        assert data["role"] == "sales_associate"

    def test_response_fields_match_openapi_schema(self):
        new_staff = make_staff()
        app.dependency_overrides[get_db] = db_override()
        client = TestClient(app)

        with patch("app.routers.auth.staff_repo.get_by_email", return_value=None), \
             patch("app.routers.auth.staff_repo.create_staff", return_value=new_staff):
            resp = client.post("/api/v1/auth/register", json=VALID)

        app.dependency_overrides.clear()

        data = resp.json()
        for field in ["access_token", "refresh_token", "token_type", "staff_id", "role"]:
            assert field in data, f"Missing field: {field}"

    def test_duplicate_email_returns_409(self):
        existing = make_staff()
        app.dependency_overrides[get_db] = db_override()
        client = TestClient(app)

        with patch("app.routers.auth.staff_repo.get_by_email", return_value=existing):
            resp = client.post("/api/v1/auth/register", json=VALID)

        app.dependency_overrides.clear()

        assert resp.status_code == 409
        assert "access_token" not in resp.json()

    def test_password_mismatch_returns_422(self):
        client = TestClient(app)
        payload = {**VALID, "confirm_password": "doesnotmatch"}
        resp = client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 422
        assert "access_token" not in resp.json()

    def test_invalid_email_returns_422(self):
        client = TestClient(app)
        payload = {**VALID, "email": "not-an-email"}
        resp = client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 422

    def test_password_too_short_returns_422(self):
        client = TestClient(app)
        payload = {**VALID, "password": "short", "confirm_password": "short"}
        resp = client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 422

    def test_invalid_role_returns_422(self):
        client = TestClient(app)
        payload = {**VALID, "role": "admin"}
        resp = client.post("/api/v1/auth/register", json=payload)
        assert resp.status_code == 422
