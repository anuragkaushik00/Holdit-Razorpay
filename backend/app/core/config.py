from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BACKEND_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE_PATH = BACKEND_ROOT / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE_PATH),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    postgres_url: str = Field(
        "postgresql+asyncpg://postgres:postgres@localhost:5432/holdit", 
        alias="POSTGRES_URL"
    )

    jwt_secret: str = Field(
        "default_dev_secret_do_not_use_in_prod", 
        alias="JWT_SECRET"
    )
    jwt_expiry: int = Field(3600, alias="JWT_EXPIRY")
    smtp_username: str = Field("", alias="SMTP_USERNAME")
    smtp_password: str = Field("", alias="SMTP_PASSWORD")
    smtp_host: str = Field("smtp.gmail.com", alias="SMTP_HOST")
    smtp_port: int = Field(587, alias="SMTP_PORT")
    smtp_from_email: str = Field("noreply@holdit.com", alias="SMTP_FROM_EMAIL")
    firebase_credentials_json: str = Field("", alias="FIREBASE_CREDENTIALS_JSON")
    aws_access_key_id: str = Field("", alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: str = Field("", alias="AWS_SECRET_ACCESS_KEY")
    aws_s3_bucket: str = Field("", alias="AWS_S3_BUCKET")
    google_client_id: str = Field("", alias="GOOGLE_CLIENT_ID")
    razorpay_key_id: str = Field("", alias="RAZORPAY_KEY_ID")
    razorpay_key_secret: str = Field("", alias="RAZORPAY_KEY_SECRET")

    # Production hardening
    sentry_dsn: str = Field("", alias="SENTRY_DSN")
    allowed_origins: str = Field(
        "http://localhost:3000,*", alias="ALLOWED_ORIGINS"
    )
    rate_limit_per_minute: int = Field(100, alias="RATE_LIMIT_PER_MINUTE")
    environment: str = Field("development", alias="ENVIRONMENT")

    # Database connection pool
    database_pool_size: int = Field(10, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(20, alias="DATABASE_MAX_OVERFLOW")
    database_pool_timeout: int = Field(30, alias="DATABASE_POOL_TIMEOUT")
    database_pool_recycle: int = Field(1800, alias="DATABASE_POOL_RECYCLE")

    # Payment configuration
    payment_expiry_minutes: int = Field(30, alias="PAYMENT_EXPIRY_MINUTES")

    # Gunicorn
    gunicorn_workers: int = Field(2, alias="GUNICORN_WORKERS")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
