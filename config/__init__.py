import logging
import os


class AppConfig:
    def __init__(self) -> None:
        missing_values = False

        database_url = os.getenv("DATABASE_URL", "")
        if database_url == "":
            logging.error("config error: missing 'database_url'")
            missing_values = True
        self.database_url = database_url

        if missing_values:
            raise ValueError("missing values")
