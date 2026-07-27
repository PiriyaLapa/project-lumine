import os
from dotenv import load_dotenv

load_dotenv()


def _require_env(name: str, hint: str = "") -> str:
    value = os.getenv(name)
    if not value:
        msg = f"Required environment variable '{name}' is not set."
        if hint:
            msg += f" {hint}"
        raise RuntimeError(msg)
    return value


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "mysql+pymysql://lumine:lumine@localhost:3306/lumine"
    )
    SECRET_KEY: str = _require_env(
        "SECRET_KEY",
        "Generate one: python3 -c \"import secrets; print(secrets.token_hex(32))\"",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    GOOGLE_DRIVE_CREDENTIALS_FILE: str = os.getenv(
        "GOOGLE_DRIVE_CREDENTIALS_FILE", "credentials.json"
    )
    SAP_COLUMN_MAP_PATH: str = os.path.join(
        os.path.dirname(__file__), "..", "config", "sap_column_map.json"
    )
    MAX_IMAGE_SIZE_KB: int = 800
    MAX_IMAGE_DIMENSION: int = 1280
    ALLOWED_ORIGINS: list = [
        o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()
    ]
    ENV: str = os.getenv("ENV", "development")

    # ------------------------------------------------------------------
    # Auto-Touch Sprint 1 — required when auto_touch_service is loaded.
    # Not guarded here so existing features start without them.
    # Each service validates its own key via _require_env() at init time.
    # ------------------------------------------------------------------
    ANTHROPIC_API_KEY: str | None = os.getenv("ANTHROPIC_API_KEY")
    SMTP_HOST: str | None = os.getenv("SMTP_HOST")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME: str | None = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD: str | None = os.getenv("SMTP_PASSWORD")
    LINE_CHANNEL_ACCESS_TOKEN: str | None = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")

    # ------------------------------------------------------------------
    # Auto-Touch automated customer messaging — send gate.
    # Defaults to disabled (False) even if the credentials above are set.
    # Sending real LINE/email messages to customers requires explicit
    # company authorization for automated customer messaging, which has
    # not been granted yet. Do NOT flip this to true in production until
    # the architect explicitly authorizes it. See
    # app/services/auto_touch_service.py (send_message gate) and
    # docs/render-env-setup.md for context — this is intentional, not a
    # missing-config bug to "fix."
    # ------------------------------------------------------------------
    AUTO_TOUCH_SEND_ENABLED: bool = os.getenv("AUTO_TOUCH_SEND_ENABLED", "false").lower() == "true"


settings = Settings()
