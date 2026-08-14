import pytest
from pydantic import ValidationError

from app.core.config import MIN_PRODUCTION_JWT_SECRET_BYTES, Settings


def test_production_security_accepts_explicit_safe_configuration() -> None:
    secret = "x" * MIN_PRODUCTION_JWT_SECRET_BYTES
    settings = Settings(
        app_env="production",
        allow_dev_user_fallback=False,
        jwt_secret_key=secret,
        cors_origins="https://creator.example.com,https://admin.example.com",
    )

    assert settings.jwt_secret_key == secret
    assert settings.cors_origin_list == [
        "https://creator.example.com",
        "https://admin.example.com",
    ]


def test_production_security_rejects_short_jwt_secret() -> None:
    with pytest.raises(ValidationError, match="at least 32 bytes"):
        Settings(
            app_env="production",
            allow_dev_user_fallback=False,
            jwt_secret_key="too-short",
            cors_origins="https://creator.example.com",
        )


def test_production_security_rejects_wildcard_cors() -> None:
    with pytest.raises(ValidationError, match="explicit origins"):
        Settings(
            app_env="production",
            allow_dev_user_fallback=False,
            jwt_secret_key="x" * MIN_PRODUCTION_JWT_SECRET_BYTES,
            cors_origins="*",
        )
