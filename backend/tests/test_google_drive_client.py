"""
TDD — Google Drive client tests.
Closes a coverage gap: app/services/google_drive_client.py had no dedicated
test file, so its real _get_service()/upload() bodies never executed —
every other test patches app.services.evidence_service.drive_client wholesale.
"""
from unittest.mock import MagicMock, patch

import pytest

from app.services import google_drive_client


@pytest.fixture(autouse=True)
def reset_cached_service():
    """_get_service() caches the client in a module global — reset between tests."""
    google_drive_client._drive_service = None
    yield
    google_drive_client._drive_service = None


# ---------------------------------------------------------------------------
# _get_service()
# ---------------------------------------------------------------------------

class TestGetService:
    def test_builds_and_caches_service_from_credentials(self):
        mock_creds = MagicMock()
        mock_service = MagicMock()

        with patch(
            "google.oauth2.service_account.Credentials.from_service_account_file",
            return_value=mock_creds,
        ) as mock_from_file, patch(
            "googleapiclient.discovery.build", return_value=mock_service
        ) as mock_build:
            result = google_drive_client._get_service()

        assert result is mock_service
        mock_from_file.assert_called_once()
        mock_build.assert_called_once_with("drive", "v3", credentials=mock_creds)

    def test_second_call_returns_cached_service_without_rebuilding(self):
        mock_service = MagicMock()

        with patch(
            "google.oauth2.service_account.Credentials.from_service_account_file",
            return_value=MagicMock(),
        ), patch("googleapiclient.discovery.build", return_value=mock_service) as mock_build:
            first = google_drive_client._get_service()
            second = google_drive_client._get_service()

        assert first is second
        mock_build.assert_called_once()  # not called again on second invocation

    def test_credentials_failure_raises_runtime_error(self):
        with patch(
            "google.oauth2.service_account.Credentials.from_service_account_file",
            side_effect=FileNotFoundError("credentials.json not found"),
        ):
            with pytest.raises(RuntimeError, match="could not be initialised"):
                google_drive_client._get_service()


# ---------------------------------------------------------------------------
# upload()
# ---------------------------------------------------------------------------

class TestUpload:
    def _mock_service(self, response: dict):
        service = MagicMock()
        service.files.return_value.create.return_value.execute.return_value = response
        return service

    def test_upload_returns_web_view_link_when_present(self, monkeypatch):
        monkeypatch.delenv("GOOGLE_DRIVE_FOLDER_ID", raising=False)
        service = self._mock_service(
            {"id": "file123", "webViewLink": "https://drive.google.com/file/view/abc"}
        )

        with patch.object(google_drive_client, "_get_service", return_value=service), \
             patch("googleapiclient.http.MediaIoBaseUpload") as mock_media:
            uri = google_drive_client.upload(b"fake_jpeg_bytes", "evidence_1_123.jpg")

        assert uri == "https://drive.google.com/file/view/abc"
        mock_media.assert_called_once()

    def test_upload_falls_back_to_constructed_uri_when_no_web_view_link(self, monkeypatch):
        monkeypatch.delenv("GOOGLE_DRIVE_FOLDER_ID", raising=False)
        service = self._mock_service({"id": "file456"})

        with patch.object(google_drive_client, "_get_service", return_value=service), \
             patch("googleapiclient.http.MediaIoBaseUpload"):
            uri = google_drive_client.upload(b"fake_jpeg_bytes", "evidence_1_123.jpg")

        assert uri == "https://drive.google.com/file/d/file456/view"

    def test_upload_includes_folder_id_when_configured(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_DRIVE_FOLDER_ID", "folder-xyz")
        service = self._mock_service({"id": "file1", "webViewLink": "https://drive/x"})

        with patch.object(google_drive_client, "_get_service", return_value=service), \
             patch("googleapiclient.http.MediaIoBaseUpload"):
            google_drive_client.upload(b"fake_jpeg_bytes", "evidence_1_123.jpg")

        _, kwargs = service.files.return_value.create.call_args
        assert kwargs["body"]["parents"] == ["folder-xyz"]

    def test_upload_omits_parents_when_folder_id_not_configured(self, monkeypatch):
        monkeypatch.delenv("GOOGLE_DRIVE_FOLDER_ID", raising=False)
        service = self._mock_service({"id": "file1", "webViewLink": "https://drive/x"})

        with patch.object(google_drive_client, "_get_service", return_value=service), \
             patch("googleapiclient.http.MediaIoBaseUpload"):
            google_drive_client.upload(b"fake_jpeg_bytes", "evidence_1_123.jpg")

        _, kwargs = service.files.return_value.create.call_args
        assert "parents" not in kwargs["body"]

    def test_upload_sends_pdpa_filename_as_metadata_name(self, monkeypatch):
        monkeypatch.delenv("GOOGLE_DRIVE_FOLDER_ID", raising=False)
        service = self._mock_service({"id": "file1", "webViewLink": "https://drive/x"})

        with patch.object(google_drive_client, "_get_service", return_value=service), \
             patch("googleapiclient.http.MediaIoBaseUpload"):
            google_drive_client.upload(b"fake_jpeg_bytes", "evidence_42_999.jpg")

        _, kwargs = service.files.return_value.create.call_args
        assert kwargs["body"]["name"] == "evidence_42_999.jpg"
