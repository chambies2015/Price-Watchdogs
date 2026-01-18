from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    database_url: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    mailgun_api_key: Optional[str] = None
    mailgun_domain: Optional[str] = None
    mailgun_from_email: Optional[str] = None
    mailgun_api_base_url: str = "https://api.mailgun.net"
    frontend_base_url: str = "http://localhost:3000"
    stripe_secret_key: Optional[str] = None
    stripe_publishable_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    sentry_dsn: Optional[str] = None
    environment: str = "development"
    cors_origins: str = "*"
    log_sample_rate: float = 0.1

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def async_database_url(self) -> str:
        if self.database_url.startswith("postgresql://"):
            return self.database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return self.database_url


settings = Settings()
