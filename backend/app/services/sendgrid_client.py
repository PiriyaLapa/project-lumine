"""
SendGrid client — transactional email wrapper.
Requires SENDGRID_API_KEY. Never logs to_email (PII).
"""
import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_SEND_URL = "https://api.sendgrid.com/v3/mail/send"
_FROM_EMAIL = "no-reply@lumine.app"


def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send a transactional email via SendGrid. Returns True on success, False on failure."""
    if not settings.SENDGRID_API_KEY:
        raise RuntimeError("SENDGRID_API_KEY is not set. Cannot send email without it.")

    response = httpx.post(
        _SEND_URL,
        headers={
            "Authorization": f"Bearer {settings.SENDGRID_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "personalizations": [{"to": [{"email": to_email}]}],
            "from": {"email": _FROM_EMAIL},
            "subject": subject,
            "content": [{"type": "text/plain", "value": body}],
        },
        timeout=10.0,
    )

    if response.status_code in (200, 202):
        logger.info("sendgrid_client: email sent successfully")
        return True

    logger.error("sendgrid_client: send failed, status=%d", response.status_code)
    return False
