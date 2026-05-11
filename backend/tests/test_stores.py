"""
TDD — GET /api/v1/stores endpoint.
Public endpoint — no JWT required.
Tests written before implementation per CLAUDE.md TDD rule.
"""
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.models.store import Store


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_store(store_id: int, name: str) -> Store:
    s = Store()
    s.id = store_id
    s.name = name
    return s


MOCK_STORES = [
    make_store(8901, "BOSS Siam Paragon"),
    make_store(8902, "BOSS Central Chidlom"),
    make_store(8904, "BOSS Icon Siam"),
    make_store(8907, "BOSS Emporium"),
    make_store(8918, "BOSS One Bangkok"),
]


def db_override_stores():
    def _inner():
        yield MagicMock()
    return _inner


# ---------------------------------------------------------------------------
# Stores endpoint
# ---------------------------------------------------------------------------

class TestStoresEndpoint:

    def test_returns_200_with_list(self):
        app.dependency_overrides[get_db] = db_override_stores()
        client = TestClient(app)

        with patch("app.routers.stores.store_repo.get_all", return_value=MOCK_STORES):
            resp = client.get("/api/v1/stores")

        app.dependency_overrides.clear()

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_list_is_not_empty(self):
        app.dependency_overrides[get_db] = db_override_stores()
        client = TestClient(app)

        with patch("app.routers.stores.store_repo.get_all", return_value=MOCK_STORES):
            resp = client.get("/api/v1/stores")

        app.dependency_overrides.clear()

        assert len(resp.json()) == 5

    def test_response_fields_match_openapi_schema(self):
        """Each store must have id (int) and name (str) — openapi.yaml Store schema."""
        app.dependency_overrides[get_db] = db_override_stores()
        client = TestClient(app)

        with patch("app.routers.stores.store_repo.get_all", return_value=MOCK_STORES):
            resp = client.get("/api/v1/stores")

        app.dependency_overrides.clear()

        for store in resp.json():
            assert "id" in store
            assert "name" in store
            assert isinstance(store["id"], int)
            assert isinstance(store["name"], str)

    def test_no_jwt_required(self):
        """Public endpoint — must return 200 without any Authorization header."""
        app.dependency_overrides[get_db] = db_override_stores()
        client = TestClient(app)

        with patch("app.routers.stores.store_repo.get_all", return_value=MOCK_STORES):
            resp = client.get("/api/v1/stores")  # no headers at all

        app.dependency_overrides.clear()

        assert resp.status_code == 200
