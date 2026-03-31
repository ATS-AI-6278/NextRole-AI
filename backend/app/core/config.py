from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Telegram
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_WEBHOOK_SECRET: Optional[str] = None
    TELEGRAM_BASE_URL: str = "http://localhost:8000"
    TELEGRAM_POLLING: bool = False

    # Gmail OAuth
    GMAIL_OAUTH_CLIENT_ID: str = ""
    GMAIL_OAUTH_CLIENT_SECRET: str = ""
    GMAIL_OAUTH_REDIRECT_URL: str = ""
    GOOGLE_API_KEY: Optional[str] = None

    # Multi-tenant data
    DATABASE_URL: str = "sqlite:///./nextrole.db"
    CHROMA_PERSIST_DIR: str = "./chroma_data"

    # Privacy/Redaction
    ENCRYPTION_KEY: str = ""

    # Server
    ENVIRONMENT: str = "dev"


settings = Settings()  # loaded from environment

