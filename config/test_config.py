from . import AppConfig


class TestAppConfig:
    def test_config(self):
        config = AppConfig()

        assert config.log_level == "info"
        assert config.database_url == "postgresql://postgres:postgres@localhost:5433"
