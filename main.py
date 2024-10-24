from dotenv import load_dotenv
from fastapi import Depends, FastAPI, status
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from slack_bolt import App

from adapter import SlackAdapter
from auth.controller import AuthControllerV1
from auth.repository import PostgresAuthRepository
from auth.service import AuthServiceV1
from auth.dto import GoogleCredentials, ProfileResponse
from bot.view import BotViewV1
from config import AppConfig, configure_logger
from chat import ChatEngineSelector
from db import config_db
from bot import Bot, BotControllerV1, BotServiceV1, PostgresBotRepository

import uvicorn

load_dotenv(override=True)


if __name__ == "__main__":
    config = AppConfig()
    
    google_credentials = GoogleCredentials(
        client_id     = config.google_client_id,
        client_secret = config.google_client_secret,
        redirect_uri  = config.google_redirect_uri,
    )

    configure_logger(config.log_level)

    sessionmaker = config_db(config.database_url)

    slack_app = App(
        token=config.slack_bot_token, signing_secret=config.slack_signing_secret
    )

    auth_repository = PostgresAuthRepository(sessionmaker)
    
    auth_service = AuthServiceV1(auth_repository, google_credentials, config.base_url, config.jwt_secret_key)
    
    auth_controller = AuthControllerV1(auth_service)

    bot_repository = PostgresBotRepository(sessionmaker)

    bot_service = BotServiceV1(bot_repository)

    bot_controller = BotControllerV1(bot_service)

    bot_view = BotViewV1(bot_controller, bot_service, auth_controller)
    

    engine_selector = ChatEngineSelector(openai_api_key=config.openai_api_key, anthropic_api_key=config.anthropic_api_key)

    slack_adapter = SlackAdapter(slack_app, engine_selector, bot_service)
    
    slack_app.event("message")(slack_adapter.event_message)

    app = FastAPI()

    app.mount("/assets", StaticFiles(directory="public"), name="assets")
    app.mount("/static", StaticFiles(directory="public"), name="static")

    app.add_api_route(
        "/",
        endpoint=bot_view.show_list_chatbots,
        response_class=HTMLResponse,
        description="Page that displays existing chatbots",
    )

    app.add_api_route(
        "/login",
        endpoint=bot_view.show_login,
        response_class=HTMLResponse,
        description="Page that displays login page",
    )

    app.add_api_route(
        "/create",
        endpoint=bot_view.show_create_chatbots,
        response_class=HTMLResponse,
        methods=["POST", "GET"],
        description="Page that displays create chatbot",
    )

    app.add_api_route(
        "/edit/{id}",
        endpoint=bot_view.show_edit_chatbot,
        response_class=HTMLResponse,
        description="Page that displays chatbot in detail",
    )

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
        "/api/bots/slug",
        lambda q: bot_controller.check_slug_exist(q),
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        name="Check Is Slug Exist"
    )
    app.add_api_route(
        "/api/bots/{bot_id}",
        endpoint=bot_controller.delete_chatbot,
        methods=["DELETE"],
        status_code=status.HTTP_204_NO_CONTENT,
    )
    app.add_api_route(
        "/api/slack/events", endpoint=slack_adapter.handle_events, methods=["POST"]
    )
    app.add_api_route("/api/slack/ask", endpoint=slack_adapter.ask, methods=["POST"])
    app.add_api_route(
        "/api/slack/list-bots", endpoint=slack_adapter.list_bots, methods=["POST"]
    )
    
    app.add_api_route(
        "/login/google",
        endpoint=auth_controller.login_redirect_google, 
        response_class=RedirectResponse,
        methods=["GET"],
        description="Page to redirect user to when using google sign-in"
    )
    
    app.add_api_route(
        "/api/auth/callback/google",
        endpoint=auth_controller.authorize_google,
        response_class=RedirectResponse,
        methods=["GET"],
    )
    
    app.add_api_route(
        "/api/auth/profile",
        endpoint=auth_controller.user_profile_google,
        response_model=ProfileResponse,
        methods=["GET"],
    )
    
    app.add_api_route(
        "/logout",
        endpoint=auth_controller.logout,
        response_class=RedirectResponse,
        methods=["GET"],
    )

    uvicorn.run(app, host="0.0.0.0", port=config.port)
