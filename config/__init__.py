import json
import logging
import os
import sys

from datetime import datetime
from loguru import logger


class InvalidLogLevelException(Exception):
    pass


class AppConfig:

    def validate_env_var(self, var_name: str) -> tuple[str, bool]:
        var = os.getenv(var_name, "")
        if var == "":
            logging.error(f"config error: missing '{var_name}'")

        return var, var != ""

    def __init__(self) -> None:
        invalid = False

        port = os.getenv("PORT", "")
        if port == "":
            self.port = 8000
        else:
            try:
                self.port = int(port)
            except ValueError:
                logging.error("config error: 'PORT' must be integer")
                invalid = True

        self.log_level, found = self.validate_env_var("LOG_LEVEL")
        if not found:
            invalid = True

        self.database_url, found = self.validate_env_var("DATABASE_URL")
        if not found:
            invalid = True

        self.slack_bot_token, found = self.validate_env_var("SLACK_BOT_TOKEN")
        if not found:
            invalid = True

        self.slack_signing_secret, found = self.validate_env_var("SLACK_SIGNING_SECRET")
        if not found:
            invalid = True

        if invalid:
            raise ValueError("invalid app config")


# For now, we only want INFO or DEBUG level logging
def parse_log_level(log_level: str) -> str:
    if log_level == "info" or log_level == "INFO":
        return "INFO"
    if log_level == "debug" or log_level == "DEBUG":
        return "DEBUG"
    raise InvalidLogLevelException("invalid log level")


# Remove default logger and configure new logger
def configure_logger(log_level: str):
    def sink(message):
        message_json = json.loads(message)
        message_json["level"] = message_json["record"]["level"]["name"]
        timestamp = message_json["record"]["time"]["timestamp"]
        message_json["timestamp"] = (
            datetime.fromtimestamp(timestamp).astimezone().isoformat()
        )
        message_json["function"] = message_json["record"]["function"]
        message_json["message"] = message_json["record"]["message"]
        if message_json["record"]["exception"] is not None:
            message_json["exception"] = message_json["record"]["exception"]
            message_json["caller"] = (
                message_json["record"]["file"]["path"]
                + ":"
                + str(message_json["record"]["line"])
            )
        message_json.update(message_json["record"]["extra"])
        message_json.pop("text")
        message_json.pop("record")

        serialized = json.dumps(message_json, default=str)
        print(serialized, file=sys.stdout, flush=True)

    level = parse_log_level(log_level)
    logger.remove(0)
    logger.add(
        sink,
        level=level,
        format="{time} | {level} | {message}",
        backtrace=True,
        serialize=True,
    )
