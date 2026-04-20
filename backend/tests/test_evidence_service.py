"""
TDD — Evidence Service tests.
Tests written BEFORE evidence_service.py logic.
All test cases from SRS §5 FR-04 and §6.6.
"""
import io
import pytest
from unittest.mock import MagicMock, patch

from app.services.evidence_service import EvidenceService, EvidenceResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_db():
    return MagicMock()


def jpeg_bytes(size_kb: float) -> bytes:
    """Return a minimal JPEG-like byte sequence of approximately size_kb kilobytes."""
    # Minimal valid JPEG header + padding to reach target size
    header = bytes([0xFF, 0xD8, 0xFF, 0xE0])  # JPEG SOI + APP0 marker
    padding = b"\x00" * max(0, int(size_kb * 1024) - len(header))
    return header + padding


# ---------------------------------------------------------------------------
# Image size validation (SRS §5 FR-04)
# ---------------------------------------------------------------------------

class TestImageSizeValidation:
    def test_image_under_800kb_passes(self):
        """Image under 800KB is accepted and uploaded without modification."""
        db = make_db()
        image = jpeg_bytes(400)  # 400KB — under limit

        with patch("app.services.evidence_service.drive_client") as mock_drive, \
             patch("app.services.evidence_service.evidence_repo") as mock_repo:
            mock_drive.upload.return_value = "https://drive.google.com/file/abc"
            mock_repo.create.return_value = MagicMock(id=1)

            result = EvidenceService.save(
                db=db,
                task_id=1,
                staff_id=10,
                notes="Good interaction.",
                image_bytes=image,
                filename="evidence_1_123.jpg",
            )

        assert result.image_uri == "https://drive.google.com/file/abc"
        assert result.image_size_kb <= 800
        mock_drive.upload.assert_called_once()

    def test_image_over_800kb_is_rejected_with_error(self):
        """
        Backend rejects images over 800KB — mobile should compress first.
        SRS §5 FR-04: mobile compresses before upload; backend enforces as safety net.
        """
        db = make_db()
        image = jpeg_bytes(900)  # 900KB — over limit

        with pytest.raises(ValueError, match="800"):
            EvidenceService.save(
                db=db,
                task_id=1,
                staff_id=10,
                notes="",
                image_bytes=image,
                filename="evidence_1_123.jpg",
            )

    def test_image_size_kb_stored_in_record(self):
        """image_size_kb is recorded in EvidenceLog for audit (SRS §5 FR-04)."""
        db = make_db()
        image = jpeg_bytes(250)

        with patch("app.services.evidence_service.drive_client") as mock_drive, \
             patch("app.services.evidence_service.evidence_repo") as mock_repo:
            mock_drive.upload.return_value = "https://drive.google.com/file/xyz"
            mock_repo.create.return_value = MagicMock(id=2)

            EvidenceService.save(
                db=db,
                task_id=5,
                staff_id=10,
                notes="",
                image_bytes=image,
                filename="evidence_5_123.jpg",
            )

        call_kwargs = mock_repo.create.call_args[1]
        assert "image_size_kb" in call_kwargs
        assert call_kwargs["image_size_kb"] == pytest.approx(250, abs=5)


# ---------------------------------------------------------------------------
# Google Drive upload (SRS §5 FR-04)
# ---------------------------------------------------------------------------

class TestDriveUpload:
    def test_filename_format_matches_srs(self):
        """
        Drive filename must be evidence_{task_id}_{timestamp}.jpg (SRS §7 NFR-03 PDPA).
        No customer PII in the filename.
        """
        db = make_db()
        image = jpeg_bytes(100)
        uploaded_filename = None

        def capture_upload(data: bytes, filename: str) -> str:
            nonlocal uploaded_filename
            uploaded_filename = filename
            return "https://drive.google.com/file/123"

        with patch("app.services.evidence_service.drive_client") as mock_drive, \
             patch("app.services.evidence_service.evidence_repo") as mock_repo:
            mock_drive.upload.side_effect = capture_upload
            mock_repo.create.return_value = MagicMock(id=1)

            EvidenceService.save(
                db=db,
                task_id=42,
                staff_id=10,
                notes="",
                image_bytes=image,
                filename="any.jpg",
            )

        assert uploaded_filename is not None
        assert uploaded_filename.startswith("evidence_42_")
        assert uploaded_filename.endswith(".jpg")
        # No customer data in filename
        assert "CUST" not in uploaded_filename

    def test_drive_failure_saves_null_uri(self):
        """
        If Google Drive upload fails → save EvidenceLog with image_uri=None.
        Do NOT raise — task completion must not be blocked (SRS §5 FR-04 + §15).
        """
        db = make_db()
        image = jpeg_bytes(200)

        with patch("app.services.evidence_service.drive_client") as mock_drive, \
             patch("app.services.evidence_service.evidence_repo") as mock_repo:
            mock_drive.upload.side_effect = Exception("Drive API unavailable")
            mock_repo.create.return_value = MagicMock(id=3)

            result = EvidenceService.save(
                db=db,
                task_id=1,
                staff_id=10,
                notes="Good call.",
                image_bytes=image,
                filename="evidence_1_123.jpg",
            )

        assert result.image_uri is None
        assert result.drive_failed is True
        # Record still created — notes saved even when image fails
        mock_repo.create.assert_called_once()
        call_kwargs = mock_repo.create.call_args[1]
        assert call_kwargs["image_uri"] is None

    def test_no_image_saves_notes_only(self):
        """Evidence with no photo (notes only) — no Drive upload, image_uri=None."""
        db = make_db()

        with patch("app.services.evidence_service.drive_client") as mock_drive, \
             patch("app.services.evidence_service.evidence_repo") as mock_repo:
            mock_repo.create.return_value = MagicMock(id=4)

            result = EvidenceService.save(
                db=db,
                task_id=1,
                staff_id=10,
                notes="Called customer, no answer.",
                image_bytes=None,
                filename=None,
            )

        mock_drive.upload.assert_not_called()
        assert result.image_uri is None
        assert result.drive_failed is False


# ---------------------------------------------------------------------------
# EvidenceLog record creation
# ---------------------------------------------------------------------------

class TestEvidenceRecordCreation:
    def test_record_contains_correct_task_id_and_staff_id(self):
        """EvidenceLog record links to the correct task and staff."""
        db = make_db()
        image = jpeg_bytes(100)

        with patch("app.services.evidence_service.drive_client") as mock_drive, \
             patch("app.services.evidence_service.evidence_repo") as mock_repo:
            mock_drive.upload.return_value = "https://drive.google.com/file/ok"
            mock_repo.create.return_value = MagicMock(id=99)

            EvidenceService.save(
                db=db,
                task_id=77,
                staff_id=33,
                notes="Follow-up done.",
                image_bytes=image,
                filename="evidence_77_123.jpg",
            )

        call_kwargs = mock_repo.create.call_args[1]
        assert call_kwargs["task_id"] == 77
        assert call_kwargs["staff_id"] == 33

    def test_notes_stored_in_record(self):
        """Notes text is saved in EvidenceLog."""
        db = make_db()

        with patch("app.services.evidence_service.drive_client") as mock_drive, \
             patch("app.services.evidence_service.evidence_repo") as mock_repo:
            mock_repo.create.return_value = MagicMock(id=5)

            EvidenceService.save(
                db=db,
                task_id=1,
                staff_id=10,
                notes="Customer was happy with the product.",
                image_bytes=None,
                filename=None,
            )

        call_kwargs = mock_repo.create.call_args[1]
        assert call_kwargs["notes"] == "Customer was happy with the product."
