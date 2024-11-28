from dotenv import load_dotenv
from fastapi import FastAPI, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from slack_bolt import App
from slack_bolt.oauth.oauth_settings import OAuthSettings

from adapter import SlackAdapter, PostgresReactionEventRepository
from adapter.slack_repository import PostgresWorkspaceDataRepository, CustomInstallationStore
from adapter.view import SlackViewV1
from auth.controller import AuthControllerV1
from auth.repository import PostgresAuthRepository
from auth.service import AuthServiceV1
from auth.dto import GoogleCredentials, ProfileResponse
from auth.view import UserViewV1
from bot.view import BotViewV1
from config import AppConfig, configure_logger
from chat import ChatEngineSelector
from data_source.view import DataSourceViewV1
from db import config_db
from bot import Bot, BotControllerV1, BotServiceV1, PostgresBotRepository

from adapter.slack_dto import SlackConfig
from document.dto import AWSConfig
from document.view import DocumentViewV1
from web.logging import RequestLoggingMiddleware

import uvicorn
import sentry_sdk
from sentry_sdk.integrations.asgi import SentryAsgiMiddleware
from sentry_sdk.integrations.threading import ThreadingIntegration
import os

from document.controller import DocumentControllerV1
from document.repository import PostgresDocumentRepository
from document.service import DocumentServiceV1

load_dotenv(override=True)

sentry_sdk.init(
    dsn=os.getenv("SENTRY_DSN"),
    traces_sample_rate=1.0,
    environment=os.getenv("ENVIRONMENT", "production"),
    integrations=[ThreadingIntegration(propagate_scope=True)],
    _experiments={
        "continuous_profiling_auto_start": True,
    },
)


if __name__ == "__main__":
    config = AppConfig()

    google_credentials = GoogleCredentials(
        client_id=config.google_client_id,
        client_secret=config.google_client_secret,
        redirect_uri=config.google_redirect_uri,
    )

    aws_config = AWSConfig(
        aws_access_key_id=config.aws_access_key_id,
        aws_secret_access_key=config.aws_secret_access_key,
        aws_public_bucket_name=config.aws_public_bucket_name,
        aws_region=config.aws_region,
        aws_endpoint_url=config.aws_endpoint_url,
    )

    slack_config = SlackConfig(
        slack_bot_token=config.slack_bot_token,
        slack_signing_secret=config.slack_signing_secret,
        slack_client_id=config.slack_client_id,
        slack_client_secret=config.slack_client_secret,
        slack_scopes=config.slack_scopes
    )
    
    configure_logger(config.log_level)

    sessionmaker = config_db(config.database_url)

    auth_repository = PostgresAuthRepository(sessionmaker)

    auth_service = AuthServiceV1(
        auth_repository,
        google_credentials,
        config.base_url,
        config.jwt_secret_key,
        config.admin_emails,
    )

    auth_controller = AuthControllerV1(auth_service)

    user_view = UserViewV1(auth_controller, auth_service, config.admin_emails)

    bot_repository = PostgresBotRepository(sessionmaker)

    bot_service = BotServiceV1(bot_repository)

    bot_controller = BotControllerV1(bot_service)

    bot_view = BotViewV1(
        bot_controller, bot_service, auth_controller, config.admin_emails
    )

    data_source_view = DataSourceViewV1(auth_controller)
    engine_selector = ChatEngineSelector(
        openai_api_key=config.openai_api_key,
        anthropic_api_key=config.anthropic_api_key,
        postgres_db=config.postgres_db,
        postgres_user=config.postgres_user,
        postgres_password=config.postgres_password,
        postgres_host=config.postgres_host,
        postgres_port=config.postgres_port,
    )

    document_repository = PostgresDocumentRepository(sessionmaker)

    document_service = DocumentServiceV1(aws_config, document_repository)

    document_controller = DocumentControllerV1(document_service)

    document_view = DocumentViewV1(document_service, auth_controller)

    reaction_event_repository = PostgresReactionEventRepository(sessionmaker)

    workspace_data_repository = PostgresWorkspaceDataRepository(sessionmaker)

    custom_instalation_store = CustomInstallationStore(workspace_data_repository)

    oauth_settings = OAuthSettings(
        client_id=config.slack_client_id,
        client_secret=config.slack_client_secret,
        scopes=config.slack_scopes,
        redirect_uri=None,
        install_path="/slack/install",
        redirect_uri_path="/api/slack/oauth_redirect",
        installation_store=custom_instalation_store,
        state_validation_enabled=False
    )

    slack_app = App(
        signing_secret=config.slack_signing_secret,
        oauth_settings=oauth_settings,
    )

    slack_adapter = SlackAdapter(
        slack_app,
        engine_selector,
        bot_service,
        reaction_event_repository,
        workspace_data_repository,
        auth_repository,
        slack_config
    )

    slack_app.event("message")(slack_adapter.event_message)
    slack_app.event("reaction_added")(slack_adapter.reaction_added)
    slack_app.event("reaction_removed")(slack_adapter.reaction_removed)

    slack_view = SlackViewV1(auth_controller, slack_config, config.admin_emails)

    app = FastAPI()
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(SentryAsgiMiddleware)

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
        "/document",
        endpoint=document_view.show_list_documents,
        response_class=HTMLResponse,
        description="Page that displays list of documents",
    )
    app.add_api_route(
        "/users",
        endpoint=user_view.view_users,
        response_class=HTMLResponse,
        description="Page that displays all users",
    )
    
    app.add_api_route(
        "/create-document",
        endpoint=document_view.new_document_view,
        response_class=HTMLResponse,
        description="Page that displays Document Creation form",
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
        name="Check Is Slug Exist",
    )
    app.add_api_route(
        "/api/bots/{bot_id}",
        endpoint=bot_controller.delete_chatbot,
        methods=["DELETE"],
        status_code=status.HTTP_204_NO_CONTENT,
    )
    app.add_api_route(
        "/api/documents",
        endpoint=document_controller.fetch_documents,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        name="Get Documents",
    )
    app.add_api_route(
        "/api/documents/id/{doc_id}",
        endpoint=document_controller.fetch_document_by_id,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        name="Fetch Document by ID",
    )
    app.add_api_route(
        "/api/documents/{object_name}",
        endpoint=document_controller.fetch_document_by_name,
        methods=["GET"],
        status_code=status.HTTP_200_OK,
        name="Fetch Document by Object Name",
    )
    app.add_api_route(
        "/api/documents",
        endpoint=document_controller.upload_document,
        methods=["POST"],
        status_code=status.HTTP_200_OK,
        name="Create and Upload Document",
    )
    app.add_api_route(
        "/api/slack/events", endpoint=slack_adapter.handle_events, methods=["POST"]
    )

    app.add_api_route(
        "/slack/install", endpoint=slack_view.install, methods=["GET"]
    )

    app.add_api_route(
        "/api/slack/oauth_redirect", endpoint=slack_adapter.oauth_redirect, methods=["GET", "POST"], response_model=None 
    )

    app.add_api_route(
        "/api/slack/interactivity",
        endpoint=slack_adapter.handle_interactions,
        methods=["POST"],
    )
    app.add_api_route(
        "/api/slack/options",
        endpoint=slack_adapter.load_options,
        methods=["POST"],
    )
    app.add_api_route("/api/slack/ask", endpoint=slack_adapter.ask, methods=["POST"])
    app.add_api_route(
        "/api/slack/askbot", endpoint=slack_adapter.ask_form, methods=["POST"]
    )
    app.add_api_route(
        "/api/slack/list-bots", endpoint=slack_adapter.list_bots, methods=["POST"]
    )

    app.add_api_route(
        "/login/google",
        endpoint=auth_controller.login_redirect_google,
        response_class=RedirectResponse,
        methods=["GET"],
        description="Page to redirect user to when using google sign-in",
    )

    app.add_api_route(
        "/api/user/get-all-user-basic-info",
        endpoint=auth_controller.get_all_users_basic_info,
        methods=["GET"],
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

    uvicorn.run(app, host="0.0.0.0", port=config.port, access_log=False)
