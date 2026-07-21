"""
LINE Messaging API client — push message wrapper.
Requires LINE_CHANNEL_ACCESS_TOKEN. Never logs line_id (treated as a
personal identifier, conservatively, even though not explicitly named
in the PII list — logging it would let it slip into logs).
"""
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_PUSH_URL = "https://api.line.me/v2/bot/message/push"


def push_message(line_id: str, message_text: str) -> bool:
    """Push a text message to a LINE user. Returns True on success, False on failure."""
    if not settings.LINE_CHANNEL_ACCESS_TOKEN:
        raise RuntimeError(
            "LINE_CHANNEL_ACCESS_TOKEN is not set. Cannot send LINE messages without it."
        )

    response = httpx.post(
        _PUSH_URL,
        headers={
            "Authorization": f"Bearer {settings.LINE_CHANNEL_ACCESS_TOKEN}",
            "Content-Type": "application/json",
        },
        json={"to": line_id, "messages": [{"type": "text", "text": message_text}]},
        timeout=10.0,
    )

    if response.status_code == 200:
        logger.info("line_client: message sent successfully")
        return True

    logger.error("line_client: send failed, status=%d", response.status_code)
    return False
