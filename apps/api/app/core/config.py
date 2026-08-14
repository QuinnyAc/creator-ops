from functools import lru_cache
from uuid import UUID

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEVELOPMENT_JWT_SECRET = "development-only-change-me-creator-ops-secret"
MIN_PRODUCTION_JWT_SECRET_BYTES = 32


class Settings(BaseSettings):
    app_name: str = "Creator Ops API"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = (
        "postgresql+psycopg://creator_ops:creator_ops@localhost:5432/creator_ops"
    )
    cors_origins: str = "http://localhost:3000"
    default_user_id: UUID = UUID("00000000-0000-0000-0000-000000000001")
    allow_dev_user_fallback: bool = True
    jwt_secret_key: str = DEVELOPMENT_JWT_SECRET
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @model_validator(mode="after")
    def validate_production_security(self) -> "Settings":
        if self.app_env == "production":
            if self.allow_dev_user_fallback:
                raise ValueError("ALLOW_DEV_USER_FALLBACK must be false in production.")
            if self.jwt_secret_key == DEVELOPMENT_JWT_SECRET:
                raise ValueError("JWT_SECRET_KEY must be changed in production.")
            if len(self.jwt_secret_key.encode("utf-8")) < MIN_PRODUCTION_JWT_SECRET_BYTES:
                raise ValueError(
                    f"JWT_SECRET_KEY must contain at least {MIN_PRODUCTION_JWT_SECRET_BYTES} bytes "
                    "in production."
                )
            if "*" in self.cors_origin_list:
                raise ValueError("CORS_ORIGINS must list explicit origins in production; '*' is unsafe.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
