from dotenv import load_dotenv
from fastapi import FastAPI, status
from slack_bolt import App

from adapter import SlackAdapter
from config import AppConfig, configure_logger
from db import config_db
from bot import Bot, BotControllerV1, BotServiceV1, PostgresBotRepository

import uvicorn

load_dotenv(override=True)


if __name__ == "__main__":
    config = AppConfig()

    configure_logger(config.log_level)

    sessionmaker = config_db(config.database_url)

    slack_app = App(
        token=config.slack_bot_token, signing_secret=config.slack_signing_secret
    )

    bot_repository = PostgresBotRepository(sessionmaker)

    bot_service = BotServiceV1(bot_repository)

    bot_controller = BotControllerV1(bot_service)

    slack_adapter = SlackAdapter(slack_app)

    app = FastAPI()

    app.add_api_route(
        "/api/bots",
        endpoint=bot_controller.fetch_chatbots,
        status_code=status.HTTP_200_OK,
        response_model=list[Bot],
    )
    app.add_api_route(
        "/api/bots",
        endpoint=bot_controller.create_chatbot,
        methods=["POST"],
        status_code=status.HTTP_201_CREATED,
    )
    app.add_api_route(
        "/api/bots/{bot_id}",
        endpoint=bot_controller.update_chatbot,
        methods=["PATCH"],
        status_code=status.HTTP_200_OK,
    )
    app.add_api_route(
        "/api/slack/events", endpoint=slack_adapter.handle_events, methods=["POST"]
    )
    app.add_api_route(
        "/api/slack/ask", endpoint=slack_adapter.ask, methods=["POST"]
    )


    uvicorn.run(app, host="0.0.0.0", port=config.port)
