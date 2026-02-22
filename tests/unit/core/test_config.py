"""
Unit tests for app/core/config/config.py

EnvConfig is a pydantic-settings model that reads from env vars / .env.
Tests use monkeypatch to inject required env vars so no real .env is needed.
"""

import pytest
from unittest.mock import patch

from app.core.config.config import EnvConfig, ConfigTypes, get_config


REQUIRED_ENV = {
    "DB_URL": "postgresql+asyncpg://user:pass@localhost/testdb",
    "DB_SYNC_URL": "postgresql+psycopg2://user:pass@localhost/testdb",
    "DB_USER": "user",
    "DB_PASSWORD": "pass",
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "DB_NAME": "testdb",
    "REDIS_PORT": "6379",
    "LOG_DIR": "/tmp/logs",
    "OBJ_DIR": "/tmp/objects",
    "MDL_DIR": "/tmp/models",
    "ALPHA_VANTAGE_API_KEY": "av-key",
    "POLYGON_API_KEY": "poly-key",
    "NEWS_API_KEY": "news-key",
}


@pytest.fixture
def env_vars(monkeypatch):
    for k, v in REQUIRED_ENV.items():
        monkeypatch.setenv(k, v)


# ---------------------------------------------------------------------------
# EnvConfig field loading
# ---------------------------------------------------------------------------

class TestEnvConfig:
    def test_loads_from_env_vars(self, env_vars):
        cfg = EnvConfig()
        assert cfg.db_url == REQUIRED_ENV["DB_URL"]
        assert cfg.db_user == "user"
        assert cfg.db_host == "localhost"
        assert cfg.db_port == "5432"
        assert cfg.redis_port == "6379"
        assert cfg.log_dir == "/tmp/logs"
        assert cfg.obj_dir == "/tmp/objects"
        assert cfg.mdl_dir == "/tmp/models"
        assert cfg.alpha_vantage_api_key == "av-key"
        assert cfg.polygon_api_key == "poly-key"
        assert cfg.news_api_key == "news-key"

    def test_missing_required_field_raises(self, monkeypatch):
        # Provide all but DB_URL
        for k, v in REQUIRED_ENV.items():
            if k != "DB_URL":
                monkeypatch.setenv(k, v)
        monkeypatch.delenv("DB_URL", raising=False)
        with pytest.raises(Exception):
            EnvConfig()

    def test_db_sync_url_field(self, env_vars):
        cfg = EnvConfig()
        assert cfg.db_sync_url == REQUIRED_ENV["DB_SYNC_URL"]


# ---------------------------------------------------------------------------
# get_config
# ---------------------------------------------------------------------------

class TestGetConfig:
    def test_returns_env_config_by_default(self, env_vars):
        cfg = get_config()
        assert isinstance(cfg, EnvConfig)

    def test_returns_env_config_for_env_type(self, env_vars):
        cfg = get_config(ConfigTypes.ENV)
        assert isinstance(cfg, EnvConfig)

    def test_unknown_type_returns_none(self, env_vars):
        # Pass a value that doesn't match any ConfigTypes branch
        # ConfigTypes only has ENV, so we'd need a different enum member.
        # Directly test the None branch by passing a non-matching mock.
        from unittest.mock import MagicMock
        fake_type = MagicMock()
        fake_type.__eq__ = lambda self, other: False
        result = get_config(fake_type)  # type: ignore[arg-type]
        assert result is None
