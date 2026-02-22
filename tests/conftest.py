"""
Top-level shared fixtures and early environment setup.

logger.py calls get_config() at import time, so required env vars must be
present before any app.* module is collected. We set them here at module
level using os.environ so they're in place before pytest collection begins.
"""

import os
import tempfile

# Create a temp directory for log files so logger.py's FileHandler doesn't
# fail when the app modules are imported during collection.
_log_tmp = tempfile.mkdtemp(prefix="fintestps_tests_")

_TEST_ENV = {
    "DB_URL": "postgresql+asyncpg://user:pass@localhost/testdb",
    "DB_SYNC_URL": "postgresql+psycopg2://user:pass@localhost/testdb",
    "DB_USER": "user",
    "DB_PASSWORD": "pass",
    "DB_HOST": "localhost",
    "DB_PORT": "5432",
    "DB_NAME": "testdb",
    "REDIS_PORT": "6379",
    "LOG_DIR": _log_tmp,
    "OBJ_DIR": "/tmp/ft_test_objects",
    "MDL_DIR": "/tmp/ft_test_models",
    "ALPHA_VANTAGE_API_KEY": "test-av-key",
    "POLYGON_API_KEY": "test-poly-key",
    "NEWS_API_KEY": "test-news-key",
}

for _k, _v in _TEST_ENV.items():
    os.environ.setdefault(_k, _v)

os.makedirs(os.environ["LOG_DIR"], exist_ok=True)
