import logging
import os


class InvalidLogLevelException(Exception):
    pass


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


# For now, we only want INFO or DEBUG level logging
def parse_log_level(log_level: str) -> str:
    if log_level == "info" or log_level == "INFO":
        return "INFO"
    if log_level == "debug" or log_level == "DEBUG":
        return "DEBUG"
    raise InvalidLogLevelException("invalid log level")
