from dotenv import load_dotenv
from fastapi import FastAPI

from bot.routes import add_bot_routes
from config import AppConfig, configure_logger
from db import config_db

import uvicorn

load_dotenv(override=True)


if __name__ == "__main__":
    config = AppConfig()

    configure_logger(config.log_level)

    sessionmaker = config_db(config.database_url)

    app = FastAPI()
    add_bot_routes(app, sessionmaker)

    uvicorn.run(app, host="0.0.0.0", port=config.port)
