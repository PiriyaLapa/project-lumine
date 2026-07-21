"""
TDD — sendgrid_client.py. Never logs to_email (PII).
"""
from unittest.mock import MagicMock, patch

from app.services import sendgrid_client


class TestSendEmail:
    def test_success_returns_true(self):
        with patch("app.services.sendgrid_client.httpx.post") as mock_post, \
             patch("app.services.sendgrid_client.settings") as mock_settings:
            mock_settings.SENDGRID_API_KEY = "test-key"
            mock_post.return_value = MagicMock(status_code=202)
            result = sendgrid_client.send_email("customer@example.com", "Hi", "Body text")
        assert result is True

    def test_failure_returns_false(self):
        with patch("app.services.sendgrid_client.httpx.post") as mock_post, \
             patch("app.services.sendgrid_client.settings") as mock_settings:
            mock_settings.SENDGRID_API_KEY = "test-key"
            mock_post.return_value = MagicMock(status_code=400, text="bad request")
            result = sendgrid_client.send_email("customer@example.com", "Hi", "Body text")
        assert result is False

    def test_missing_key_raises(self):
        with patch("app.services.sendgrid_client.settings") as mock_settings:
            mock_settings.SENDGRID_API_KEY = None
            try:
                sendgrid_client.send_email("customer@example.com", "Hi", "Body text")
                assert False, "expected RuntimeError"
            except RuntimeError:
                pass

    def test_email_never_logged(self):
        with patch("app.services.sendgrid_client.httpx.post") as mock_post, \
             patch("app.services.sendgrid_client.settings") as mock_settings, \
             patch("app.services.sendgrid_client.logger") as mock_logger:
            mock_settings.SENDGRID_API_KEY = "test-key"
            mock_post.return_value = MagicMock(status_code=202)
            sendgrid_client.send_email("secret@example.com", "Hi", "Body text")

        all_log_text = " ".join(str(c) for c in mock_logger.info.call_args_list + mock_logger.error.call_args_list)
        assert "secret@example.com" not in all_log_text
