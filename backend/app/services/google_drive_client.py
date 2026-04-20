"""
Google Drive client wrapper.
In production: authenticates via credentials.json (service account).
In tests: this module is patched at app.services.evidence_service.drive_client.

Real implementation requires GOOGLE_DRIVE_CREDENTIALS_PATH env var pointing
to a service account JSON file and a target GOOGLE_DRIVE_FOLDER_ID.
"""
import logging
import os

logger = logging.getLogger(__name__)

_drive_service = None


def _get_service():
    """Lazy-init Google Drive API service. Raises if credentials not configured."""
    global _drive_service
    if _drive_service is not None:
        return _drive_service

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        creds_path = os.environ.get("GOOGLE_DRIVE_CREDENTIALS_PATH", "credentials.json")
        credentials = service_account.Credentials.from_service_account_file(
            creds_path,
            scopes=["https://www.googleapis.com/auth/drive.file"],
        )
        _drive_service = build("drive", "v3", credentials=credentials)
        return _drive_service
    except Exception as exc:
        raise RuntimeError(f"Google Drive service could not be initialised: {exc}") from exc


def upload(data: bytes, filename: str) -> str:
    """
    Upload bytes to Google Drive.

    Args:
        data: raw image bytes
        filename: PDPA-compliant filename (evidence_{task_id}_{timestamp}.jpg)

    Returns:
        Shareable URI string for storing in EvidenceLog.image_uri

    Raises:
        Any exception from the Drive API — callers must handle gracefully.
    """
    import io
    from googleapiclient.http import MediaIoBaseUpload

    service = _get_service()
    folder_id = os.environ.get("GOOGLE_DRIVE_FOLDER_ID")

    file_metadata = {"name": filename}
    if folder_id:
        file_metadata["parents"] = [folder_id]

    media = MediaIoBaseUpload(io.BytesIO(data), mimetype="image/jpeg")
    uploaded = (
        service.files()
        .create(body=file_metadata, media_body=media, fields="id,webViewLink")
        .execute()
    )

    uri = uploaded.get("webViewLink") or f"https://drive.google.com/file/d/{uploaded['id']}/view"
    logger.info("Uploaded %s → %s", filename, uri)
    return uri
