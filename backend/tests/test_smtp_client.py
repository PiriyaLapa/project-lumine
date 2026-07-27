"""
TDD — smtp_client.py. Never logs to_email (PII).
"""
import smtplib
from unittest.mock import MagicMock, patch

from app.services import smtp_client


class TestSendEmail:
    def test_success_returns_true(self):
        with patch("app.services.smtp_client.smtplib.SMTP") as MockSMTP, \
             patch("app.services.smtp_client.settings") as mock_settings:
            mock_settings.SMTP_HOST = "smtp.gmail.com"
            mock_settings.SMTP_PORT = 587
            mock_settings.SMTP_USERNAME = "test@lumine.app"
            mock_settings.SMTP_PASSWORD = "test-password"
            mock_server = MockSMTP.return_value.__enter__.return_value
            result = smtp_client.send_email("customer@example.com", "Hi", "Body text")

        assert result is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("test@lumine.app", "test-password")
        mock_server.sendmail.assert_called_once()

    def test_failure_returns_false(self):
        with patch("app.services.smtp_client.smtplib.SMTP") as MockSMTP, \
             patch("app.services.smtp_client.settings") as mock_settings:
            mock_settings.SMTP_HOST = "smtp.gmail.com"
            mock_settings.SMTP_PORT = 587
            mock_settings.SMTP_USERNAME = "test@lumine.app"
            mock_settings.SMTP_PASSWORD = "test-password"
            mock_server = MockSMTP.return_value.__enter__.return_value
            mock_server.login.side_effect = smtplib.SMTPAuthenticationError(535, b"bad credentials")
            result = smtp_client.send_email("customer@example.com", "Hi", "Body text")

        assert result is False

    def test_connection_error_returns_false(self):
        """Network-level failures (not smtplib-specific) must also return False, not raise."""
        with patch("app.services.smtp_client.smtplib.SMTP") as MockSMTP, \
             patch("app.services.smtp_client.settings") as mock_settings:
            mock_settings.SMTP_HOST = "smtp.gmail.com"
            mock_settings.SMTP_PORT = 587
            mock_settings.SMTP_USERNAME = "test@lumine.app"
            mock_settings.SMTP_PASSWORD = "test-password"
            MockSMTP.side_effect = ConnectionRefusedError("connection refused")
            result = smtp_client.send_email("customer@example.com", "Hi", "Body text")

        assert result is False

    def test_missing_credentials_raises(self):
        with patch("app.services.smtp_client.settings") as mock_settings:
            mock_settings.SMTP_HOST = None
            mock_settings.SMTP_USERNAME = None
            mock_settings.SMTP_PASSWORD = None
            try:
                smtp_client.send_email("customer@example.com", "Hi", "Body text")
                assert False, "expected RuntimeError"
            except RuntimeError:
                pass

    def test_email_never_logged(self):
        with patch("app.services.smtp_client.smtplib.SMTP") as MockSMTP, \
             patch("app.services.smtp_client.settings") as mock_settings, \
             patch("app.services.smtp_client.logger") as mock_logger:
            mock_settings.SMTP_HOST = "smtp.gmail.com"
            mock_settings.SMTP_PORT = 587
            mock_settings.SMTP_USERNAME = "test@lumine.app"
            mock_settings.SMTP_PASSWORD = "test-password"
            smtp_client.send_email("secret@example.com", "Hi", "Body text")

        all_log_text = " ".join(str(c) for c in mock_logger.info.call_args_list + mock_logger.error.call_args_list)
        assert "secret@example.com" not in all_log_text
