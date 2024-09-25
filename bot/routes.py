from bot import BotControllerV1, PostgresBotRepository, BotServiceV1
from fastapi import FastAPI, status
from bot import Bot, BotControllerV1, BotServiceV1, PostgresBotRepository

def add_bot_routes(app: FastAPI, sessionmaker):
    bot_repository = PostgresBotRepository(sessionmaker)
    bot_service = BotServiceV1(bot_repository)
    bot_controller = BotControllerV1(bot_service)
    
    app.add_api_route(
        "/api/v1/bots",
        endpoint=bot_controller.fetch_chatbots,
        status_code=status.HTTP_200_OK,
        response_model=list[Bot],
    )
    app.add_api_route(
        "/api/v1/bots",
        endpoint=bot_controller.create_chatbot,
        methods=["POST"],
        status_code=status.HTTP_201_CREATED,
    )