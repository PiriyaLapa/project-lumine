import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "mysql+pymysql://lumine:lumine@localhost:3306/lumine"
    )
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me-in-production")
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


settings = Settings()
