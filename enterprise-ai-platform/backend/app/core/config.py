from __future__ import annotations

from enum import Enum
from functools import lru_cache
from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):  # noqa: UP042 - keeps local verification compatible with Python 3.9.
    local = "local"
    test = "test"
    development = "development"
    staging = "staging"
    production = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="EAKP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Environment = Environment.local
    service_name: str = "enterprise-ai-platform-api"
    api_version: str = "v1"
    log_level: str = "INFO"
    host: str = "0.0.0.0"  # noqa: S104 - API containers intentionally bind all interfaces.
    port: Annotated[int, Field(ge=1, le=65535)] = 8000
    reload: bool = False
    database_url: str = "sqlite:///./.local/eakp.db"
    auto_create_schema: bool = True
    jwt_secret_key: str = "dev-only-change-me-dev-only-change-me"  # noqa: S105
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: Annotated[int, Field(ge=1, le=1440)] = 30
    refresh_token_expire_days: Annotated[int, Field(ge=1, le=90)] = 14
    storage_root: str = ".local/storage"
    max_upload_size_bytes: Annotated[int, Field(ge=1)] = 25 * 1024 * 1024
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:8501",
            "http://localhost:3000",
        ]
    )
    readiness_dependencies_enabled: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
