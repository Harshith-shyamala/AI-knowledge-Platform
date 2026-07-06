from app.core.config import Environment, Settings


def test_settings_defaults_are_local_development_friendly() -> None:
    settings = Settings()

    assert settings.environment == Environment.local
    assert settings.service_name == "enterprise-ai-platform-api"
    assert settings.port == 8000
    assert settings.readiness_dependencies_enabled is False

