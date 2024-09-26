from dotenv import load_dotenv
from loguru import logger

from . import AppConfig, InvalidLogLevelException, parse_log_level, configure_logger

import pytest


class TestAppConfig:
    @pytest.fixture(autouse=True)
    def setup_dotenv(self):
        load_dotenv()

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

    def test_config_empty_slack_signing_secret(self, monkeypatch):
        monkeypatch.setenv("SLACK_SIGNING_SECRET", "")

        with pytest.raises(ValueError, match="invalid app config"):
            AppConfig()

    def test_config(self, monkeypatch):
        monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-slack-bot-token")
        monkeypatch.setenv("SLACK_SIGNING_SECRET", "slack-signing-secret")

        config = AppConfig()

        assert config.log_level == "info"
        assert config.database_url == "postgresql://postgres:postgres@localhost:5433"
        assert config.port == 8000
        assert config.slack_bot_token == "xoxb-slack-bot-token"
        assert config.slack_signing_secret == "slack-signing-secret"

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
