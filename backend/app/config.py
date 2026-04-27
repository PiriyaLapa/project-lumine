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
        os.path.dirname(__file__), "..", "..", "config", "sap_column_map.json"
    )
    MAX_IMAGE_SIZE_KB: int = 800
    MAX_IMAGE_DIMENSION: int = 1280
    ALLOWED_ORIGINS: list = [
        o.strip() for o in os.getenv("ALLOWED_ORIGINS", "").split(",") if o.strip()
    ]
    ENV: str = os.getenv("ENV", "development")


settings = Settings()
