from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import Environment, Settings
from app.factory import create_app


@pytest.fixture
def test_settings(tmp_path: Path) -> Settings:
    return Settings(
        environment=Environment.test,
        service_name="enterprise-ai-platform-api-test",
        database_url="sqlite://",
        auto_create_schema=True,
        storage_root=str(tmp_path / "storage"),
        readiness_dependencies_enabled=False,
    )


@pytest.fixture
def client(test_settings: Settings) -> Generator[TestClient, None, None]:
    app = create_app(test_settings)
    with TestClient(app) as test_client:
        yield test_client
