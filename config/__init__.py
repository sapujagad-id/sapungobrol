import logging
import os


class AppConfig:
    def __init__(self) -> None:
        missing_values = False

        log_level = os.getenv("LOG_LEVEL", "")
        if log_level == "":
            logging.error("config error: missing 'LOG_LEVEL'")
            missing_values = True
        self.log_level = log_level

        database_url = os.getenv("DATABASE_URL", "")
        if database_url == "":
            logging.error("config error: missing 'DATABASE_URL'")
            missing_values = True
        self.database_url = database_url

        if missing_values:
            raise ValueError("missing values")
