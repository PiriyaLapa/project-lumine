"""
TDD — GET /api/v1/evidence/{task_id} and PATCH /api/v1/evidence/{evidence_id}
Tests written before implementation per CLAUDE.md TDD rule.
"""
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.database import get_db
from app.services.auth_service import AuthService
from app.models.evidence_log import EvidenceLog


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_token(staff_id=1, role="sales_associate", store_id=8901):
    return AuthService.create_access_token(
        {"staff_id": staff_id, "role": role, "store_id": store_id}
    )


def make_evidence(
    id=5, task_id=10, staff_id=1,
    notes="Great call", image_uri="https://drive/x", image_size_kb=120,
):
    e = EvidenceLog()
    e.id = id
    e.task_id = task_id
    e.staff_id = staff_id
    e.notes = notes
    e.image_uri = image_uri
    e.image_size_kb = image_size_kb
    e.timestamp = "2026-05-16T10:00:00"
    return e


def db_override():
    def _inner():
        yield MagicMock()
    return _inner


AUTH = {"Authorization": f"Bearer {make_token()}"}
MGR  = {"Authorization": f"Bearer {make_token(staff_id=99, role='store_manager')}"}


# ---------------------------------------------------------------------------
# GET /api/v1/evidence/{task_id}
# ---------------------------------------------------------------------------

class TestGetEvidence:

    def test_returns_200_with_evidence(self):
        ev = make_evidence()
        app.dependency_overrides[get_db] = db_override()
        client = TestClient(app)
        with patch("app.routers.evidence.evidence_repo.get_by_task_id", return_value=ev):
            resp = client.get("/api/v1/evidence/10", headers=AUTH)
        app.dependency_overrides.clear()
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 5
        assert data["task_id"] == 10
        assert data["notes"] == "Great call"
        assert data["image_uri"] == "https://drive/x"

    def test_returns_404_when_no_evidence(self):
        app.dependency_overrides[get_db] = db_override()
        client = TestClient(app)
        with patch("app.routers.evidence.evidence_repo.get_by_task_id", return_value=None):
            resp = client.get("/api/v1/evidence/999", headers=AUTH)
        app.dependency_overrides.clear()
        assert resp.status_code == 404

    def test_no_token_returns_403(self):
        client = TestClient(app)
        resp = client.get("/api/v1/evidence/10")
        assert resp.status_code == 403

    def test_response_fields_match_openapi_schema(self):
        ev = make_evidence()
        app.dependency_overrides[get_db] = db_override()
        client = TestClient(app)
        with patch("app.routers.evidence.evidence_repo.get_by_task_id", return_value=ev):
            resp = client.get("/api/v1/evidence/10", headers=AUTH)
        app.dependency_overrides.clear()
        for field in ["id", "task_id", "notes", "image_uri", "image_size_kb", "timestamp"]:
            assert field in resp.json(), f"Missing field: {field}"


# ---------------------------------------------------------------------------
# PATCH /api/v1/evidence/{evidence_id}
# ---------------------------------------------------------------------------

class TestPatchEvidence:

    def test_patch_notes_only_keeps_existing_photo(self):
        ev = make_evidence()
        updated = make_evidence(notes="Updated notes")
        app.dependency_overrides[get_db] = db_override()
        client = TestClient(app)
        with patch("app.routers.evidence.evidence_repo.get_by_id", return_value=ev), \
             patch("app.routers.evidence.EvidenceService.update", return_value=updated):
            resp = client.patch(
                "/api/v1/evidence/5",
                data={"notes": "Updated notes"},
                headers=AUTH,
            )
        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert resp.json()["notes"] == "Updated notes"
        assert resp.json()["image_uri"] == "https://drive/x"

    def test_patch_new_photo_updates_image_uri(self):
        ev = make_evidence()
        updated = make_evidence(image_uri="https://drive/new")
        app.dependency_overrides[get_db] = db_override()
        client = TestClient(app)
        with patch("app.routers.evidence.evidence_repo.get_by_id", return_value=ev), \
             patch("app.routers.evidence.EvidenceService.update", return_value=updated):
            resp = client.patch(
                "/api/v1/evidence/5",
                data={},
                files={"image": ("photo.jpg", b"fake_jpeg_bytes", "image/jpeg")},
                headers=AUTH,
            )
        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert resp.json()["image_uri"] == "https://drive/new"

    def test_patch_no_fields_returns_200_unchanged(self):
        ev = make_evidence()
        app.dependency_overrides[get_db] = db_override()
        client = TestClient(app)
        with patch("app.routers.evidence.evidence_repo.get_by_id", return_value=ev), \
             patch("app.routers.evidence.EvidenceService.update", return_value=ev):
            resp = client.patch("/api/v1/evidence/5", data={}, headers=AUTH)
        app.dependency_overrides.clear()
        assert resp.status_code == 200
        assert resp.json()["notes"] == "Great call"
        assert resp.json()["image_uri"] == "https://drive/x"

    def test_patch_wrong_staff_returns_403(self):
        ev = make_evidence(staff_id=99)  # belongs to staff 99
        app.dependency_overrides[get_db] = db_override()
        client = TestClient(app)  # token is staff_id=1
        with patch("app.routers.evidence.evidence_repo.get_by_id", return_value=ev):
            resp = client.patch(
                "/api/v1/evidence/5",
                data={"notes": "sneaky"},
                headers=AUTH,
            )
        app.dependency_overrides.clear()
        assert resp.status_code == 403

    def test_patch_not_found_returns_404(self):
        app.dependency_overrides[get_db] = db_override()
        client = TestClient(app)
        with patch("app.routers.evidence.evidence_repo.get_by_id", return_value=None):
            resp = client.patch("/api/v1/evidence/999", data={}, headers=AUTH)
        app.dependency_overrides.clear()
        assert resp.status_code == 404

    def test_patch_no_token_returns_403(self):
        client = TestClient(app)
        resp = client.patch("/api/v1/evidence/5", data={"notes": "x"})
        assert resp.status_code == 403

    def test_manager_can_patch_any_staff_evidence(self):
        ev = make_evidence(staff_id=1)  # belongs to staff 1
        updated = make_evidence(staff_id=1, notes="Manager edit")
        app.dependency_overrides[get_db] = db_override()
        client = TestClient(app)
        with patch("app.routers.evidence.evidence_repo.get_by_id", return_value=ev), \
             patch("app.routers.evidence.EvidenceService.update", return_value=updated):
            resp = client.patch(
                "/api/v1/evidence/5",
                data={"notes": "Manager edit"},
                headers=MGR,
            )
        app.dependency_overrides.clear()
        assert resp.status_code == 200
