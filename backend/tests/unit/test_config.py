"""Unit tests for configuration."""
import os
from shinkei.config import Settings

def test_settings_load_defaults():
    """Test that settings load with default values."""
    settings = Settings()
    assert settings.app_name == "Shinkei"
    assert settings.api_v1_prefix == "/api/v1"
    assert settings.environment == "development"

def test_settings_load_env_vars(monkeypatch):
    """Test that settings load from environment variables."""
    monkeypatch.setenv("APP_NAME", "Test App")
    monkeypatch.setenv("ENVIRONMENT", "production")
    
    settings = Settings()
    assert settings.app_name == "Test App"
    assert settings.environment == "production"
