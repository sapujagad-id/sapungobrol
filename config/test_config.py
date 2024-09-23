from . import AppConfig


class TestAppConfig:
    def test_config(self):
        config = AppConfig()

        assert config.database_url == "postgres://postgres:postgres@localhost:5432"
