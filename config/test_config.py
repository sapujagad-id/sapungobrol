import pytest
from loguru import logger

from . import (AppConfig, InvalidLogLevelException, configure_logger,
               parse_log_level)


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
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-api-key")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-api-key")
        monkeypatch.setenv("TOTAL_ACCESS_LEVELS", "5")
        monkeypatch.setenv("ADMIN_EMAILS", "admin@broom.id,user@broom.id")
        monkeypatch.setenv("AWS_PUBLIC_BUCKET_NAME", "test")
        monkeypatch.setenv("AWS_REGION", "ap-test")
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
        monkeypatch.setenv("POSTGRES_DB", "test")
        monkeypatch.setenv("POSTGRES_USER", "test")
        monkeypatch.setenv("POSTGRES_PASSWORD", "test")
        monkeypatch.setenv("POSTGRES_HOST", "test")
        monkeypatch.setenv("POSTGRES_PORT", "5432")
        monkeypatch.setenv("AWS_ENDPOINT_URL", "test")

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

    def test_config_empty_total_access_levels(self, monkeypatch):
        monkeypatch.setenv("TOTAL_ACCESS_LEVELS", "")

        with pytest.raises(ValueError, match="invalid app config"):
            AppConfig()

    def test_config_empty_admin_email(self, monkeypatch):
        monkeypatch.setenv("ADMIN_EMAILS", "")

        with pytest.raises(ValueError, match="invalid app config"):
            AppConfig()


    def test_config(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-api-key")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-api-key")
        monkeypatch.setenv("TOTAL_ACCESS_LEVELS", "5")
        monkeypatch.setenv("AWS_PUBLIC_BUCKET_NAME", "test")
        monkeypatch.setenv("AWS_REGION", "ap-test")
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
        monkeypatch.setenv("AWS_ENDPOINT_URL", "test")
        monkeypatch.setenv("ADMIN_EMAILS", "admin@broom.id,user@broom.id")
        monkeypatch.setenv("POSTGRES_DB", "test")
        monkeypatch.setenv("POSTGRES_USER", "test")
        monkeypatch.setenv("POSTGRES_PASSWORD", "test")
        monkeypatch.setenv("POSTGRES_HOST", "test")
        monkeypatch.setenv("POSTGRES_PORT", "5432")

        config = AppConfig()

        assert config.log_level == "info"
        assert config.database_url == "postgresql://postgres:postgres@localhost:5433"
        assert config.port == 8000
        assert config.slack_bot_token == "xoxb-slack-bot-token"
        assert config.slack_signing_secret == "slack-signing-secret"
        assert config.openai_api_key == "test-openai-api-key"
        assert config.google_client_id != ("" or None)
        assert config.google_client_secret != ("" or None)
        assert config.google_redirect_uri.startswith("http") == True
        assert config.base_url.startswith("http") == True

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

    def test_configure_empty_openai(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "")

        with pytest.raises(ValueError, match="invalid app config"):
            AppConfig()
            
    def test_config_empty_google_client_id(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_CLIENT_ID", "")

        with pytest.raises(ValueError, match="invalid app config"):
            AppConfig()
    
    def test_config_empty_google_client_secret(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "")

        with pytest.raises(ValueError, match="invalid app config"):
            AppConfig()
    
    def test_config_empty_google_redirect_uri(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_REDIRECT_URI", "")

        with pytest.raises(ValueError, match="invalid app config"):
            AppConfig()
            
    def test_config_empty_base_url(self, monkeypatch):
        monkeypatch.setenv("BASE_URL", "")

        with pytest.raises(ValueError, match="invalid app config"):
            AppConfig()
    
    def test_configure_empty_anthropic(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "")

        with pytest.raises(ValueError, match="invalid app config"):
            AppConfig()

    def test_configure_empty_postgres_db(self, monkeypatch):
        monkeypatch.setenv("POSTGRES_DB", "")
        
        with pytest.raises(ValueError, match="invalid app config"):
            AppConfig()

    def test_configure_empty_postgres_user(self, monkeypatch):
        monkeypatch.setenv("POSTGRES_USER", "")

        with pytest.raises(ValueError, match="invalid app config"):
            AppConfig()

    def test_configure_empty_postgres_password(self, monkeypatch):
        monkeypatch.setenv("POSTGRES_PASSWORD", "")

        with pytest.raises(ValueError, match="invalid app config"):
            AppConfig()

    def test_configure_empty_postgres_host(self, monkeypatch):
        monkeypatch.setenv("POSTGRES_HOST", "")

        with pytest.raises(ValueError, match="invalid app config"):
            AppConfig()
    
    def test_configure_default_postgres_port(self, monkeypatch):
        monkeypatch.setenv("PORT", "")
        monkeypatch.setenv("OPENAI_API_KEY", "test-openai-api-key")
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-api-key")
        monkeypatch.setenv("TOTAL_ACCESS_LEVELS", "5")
        monkeypatch.setenv("ADMIN_EMAILS", "admin@broom.id,user@broom.id")
        monkeypatch.setenv("POSTGRES_DB", "test")
        monkeypatch.setenv("POSTGRES_USER", "test")
        monkeypatch.setenv("POSTGRES_PASSWORD", "test")
        monkeypatch.setenv("POSTGRES_HOST", "test")
        monkeypatch.setenv("POSTGRES_PORT", "5432")
        monkeypatch.setenv("AWS_PUBLIC_BUCKET_NAME", "test")
        monkeypatch.setenv("AWS_REGION", "ap-test")
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
        monkeypatch.setenv("AWS_ENDPOINT_URL", "test")

        config = AppConfig()

        assert config.postgres_port == 5432

    def test_configure_invalid_postgres_port(self, monkeypatch):
        monkeypatch.setenv("POSTGRES_PORT", "invalid_port")

        with pytest.raises(ValueError, match="invalid app config"):
            AppConfig()
            
