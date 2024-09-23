import logging
import os


class AppConfig:

    def validate_env_var(self, var_name: str) -> tuple[str, bool]:
        var = os.getenv(var_name, "")
        if var == "":
            logging.error(f"config error: missing '{var_name}'")

        return var, var != ""

    def __init__(self) -> None:
        missing_values = False

        self.log_level, valid = self.validate_env_var("LOG_LEVEL")
        if not valid:
            missing_values = True

        self.database_url, valid = self.validate_env_var("DATABASE_URL")
        if not valid:
            missing_values = True

        if missing_values:
            raise ValueError("missing values")
