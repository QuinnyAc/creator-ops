from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Creator Ops API"
    app_env: str = "development"
    api_v1_prefix: str = "/api/v1"
    database_url: str = (
        "postgresql+psycopg://creator_ops:creator_ops@localhost:5432/creator_ops"
    )
    cors_origins: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
