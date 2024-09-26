from loguru import logger

from . import AppConfig, InvalidLogLevelException, parse_log_level, configure_logger

import pytest


class TestAppConfig:
    def test_config_empty_database_url(self, monkeypatch):
        monkeypatch.setenv("DATABASE_URL", "")

        with pytest.raises(ValueError, match="invalid app config"):
            AppConfig()

    def test_config_empty_log_level(self, monkeypatch):
        monkeypatch.setenv("LOG_LEVEL", "")

        with pytest.raises(ValueError, match="invalid app config"):
            AppConfig()

    def test_config_invalid_port(self, monkeypatch):
        monkeypatch.setenv("PORT", "abcd")

        with pytest.raises(ValueError, match="invalid app config"):
            AppConfig()

    def test_config_default_port(self, monkeypatch):
        monkeypatch.setenv("PORT", "")

        config = AppConfig()

        assert config.port == 8000

    def test_config_empty_slack_bot_token(self, monkeypatch):
        monkeypatch.setenv("SLACK_BOT_TOKEN", "")

        with pytest.raises(ValueError, match="invalid app config"):
            AppConfig()

    def test_config(self):
        config = AppConfig()

        assert config.log_level == "info"
        assert config.database_url == "postgresql://postgres:postgres@localhost:5433"
        assert config.port == 8000
        assert config.slack_bot_token == "xoxb-slack-bot-token"

    def test_parse_log_level(self):
        assert parse_log_level("info") == "INFO"
        assert parse_log_level("debug") == "DEBUG"
        assert parse_log_level("INFO") == "INFO"
        assert parse_log_level("DEBUG") == "DEBUG"

        with pytest.raises(InvalidLogLevelException):
            parse_log_level("error")

        with pytest.raises(InvalidLogLevelException):
            parse_log_level("inFO")

    # Arbitrary test since nothing is actually worth testing here
    def test_configure_logger(self):
        configure_logger("info")

        logger.info("Test is working")

        with logger.catch():
            raise ValueError
