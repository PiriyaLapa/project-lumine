"""
SMTP client — transactional email wrapper (company email account).
Requires SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD. Never logs to_email (PII).
"""
import logging
import smtplib
from email.mime.text import MIMEText

from app.config import settings

logger = logging.getLogger(__name__)


def send_email(to_email: str, subject: str, body: str) -> bool:
    """Send a transactional email via SMTP. Returns True on success, False on failure."""
    if not settings.SMTP_HOST or not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        raise RuntimeError(
            "SMTP_HOST/SMTP_USERNAME/SMTP_PASSWORD are not set. Cannot send email without them."
        )

    message = MIMEText(body, "plain")
    message["Subject"] = subject
    message["From"] = settings.SMTP_USERNAME
    message["To"] = to_email

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
            server.sendmail(settings.SMTP_USERNAME, [to_email], message.as_string())
    except (smtplib.SMTPException, OSError) as exc:
        # smtplib has no HTTP-status concept — every failure mode (auth,
        # connection, recipient-refused) is an exception. Caught here so the
        # bool contract matches sendgrid_client.py's (status-code-based)
        # behavior for the caller in auto_touch_service.py.
        logger.error("smtp_client: send failed, error=%s", type(exc).__name__)
        return False

    logger.info("smtp_client: email sent successfully")
    return True
