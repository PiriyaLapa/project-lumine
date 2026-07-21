"""
TDD — line_client.py. Never logs line_id (personal identifier, treated
conservatively as PII-adjacent even though not explicitly named in the
PII list).
"""
from unittest.mock import MagicMock, patch

from app.services import line_client


class TestPushMessage:
    def test_success_returns_true(self):
        with patch("app.services.line_client.httpx.post") as mock_post, \
             patch("app.services.line_client.settings") as mock_settings:
            mock_settings.LINE_CHANNEL_ACCESS_TOKEN = "test-token"
            mock_post.return_value = MagicMock(status_code=200)
            result = line_client.push_message("U1234567890", "Hello!")
        assert result is True

    def test_failure_returns_false(self):
        with patch("app.services.line_client.httpx.post") as mock_post, \
             patch("app.services.line_client.settings") as mock_settings:
            mock_settings.LINE_CHANNEL_ACCESS_TOKEN = "test-token"
            mock_post.return_value = MagicMock(status_code=400, text="bad request")
            result = line_client.push_message("U1234567890", "Hello!")
        assert result is False

    def test_missing_token_raises(self):
        with patch("app.services.line_client.settings") as mock_settings:
            mock_settings.LINE_CHANNEL_ACCESS_TOKEN = None
            try:
                line_client.push_message("U1234567890", "Hello!")
                assert False, "expected RuntimeError"
            except RuntimeError:
                pass

    def test_line_id_never_logged(self):
        with patch("app.services.line_client.httpx.post") as mock_post, \
             patch("app.services.line_client.settings") as mock_settings, \
             patch("app.services.line_client.logger") as mock_logger:
            mock_settings.LINE_CHANNEL_ACCESS_TOKEN = "test-token"
            mock_post.return_value = MagicMock(status_code=200)
            line_client.push_message("U_SECRET_ID", "Hello!")

        all_log_text = " ".join(str(c) for c in mock_logger.info.call_args_list + mock_logger.error.call_args_list)
        assert "U_SECRET_ID" not in all_log_text
