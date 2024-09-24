from dotenv import load_dotenv
from fastapi import FastAPI, status

from config import AppConfig, configure_logger
from db import config_db
from bot import Bot, BotControllerV1, BotServiceV1, PostgresBotRepository

import uvicorn

load_dotenv(override=True)


if __name__ == "__main__":
    config = AppConfig()

    configure_logger(config.log_level)

    sessionmaker = config_db(config.database_url)

    bot_repository = PostgresBotRepository(sessionmaker)

    bot_service = BotServiceV1(bot_repository)

    bot_controller = BotControllerV1(bot_service)

    app = FastAPI()

    app.add_api_route(
        "/bots",
        endpoint=bot_controller.fetch_chatbots,
        status_code=status.HTTP_200_OK,
        response_model=list[Bot],
    )
    app.add_api_route(
        "/bots",
        endpoint=bot_controller.create_chatbot,
        methods=["POST"],
        status_code=status.HTTP_201_CREATED,
    )

    uvicorn.run(app, host="0.0.0.0", port=config.port)
