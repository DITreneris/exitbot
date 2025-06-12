import os
import secrets
from typing import Optional


class Settings:
    PROJECT_NAME: str = "ExitBot"
    API_V1_STR: str = "/api/v1"

    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./test.db")

    # JWT settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", secrets.token_urlsafe(32))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # Admin user settings
    FIRST_ADMIN_EMAIL: Optional[str] = os.getenv("FIRST_ADMIN_EMAIL")
    FIRST_ADMIN_PASSWORD: Optional[str] = os.getenv("FIRST_ADMIN_PASSWORD")

    # CORS settings
    BACKEND_CORS_ORIGINS: list = ["*"]

    # Logging settings
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
