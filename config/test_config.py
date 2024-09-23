import pytest

from . import AppConfig, InvalidLogLevelException, parse_log_level


class TestAppConfig:
    def test_config(self):
        config = AppConfig()

        assert config.log_level == "info"
        assert config.database_url == "postgresql://postgres:postgres@localhost:5433"

    def test_parse_log_level(self):
        config = AppConfig()

        assert parse_log_level("info") == "INFO"
        assert parse_log_level("debug") == "DEBUG"
        assert parse_log_level("INFO") == "INFO"
        assert parse_log_level("DEBUG") == "DEBUG"

        with pytest.raises(InvalidLogLevelException):
            parse_log_level("error")

        with pytest.raises(InvalidLogLevelException):
            parse_log_level("inFO")
