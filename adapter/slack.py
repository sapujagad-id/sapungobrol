import asyncio
import json
import threading
from typing import Dict
from uuid import uuid4

from typing import Any, Dict
import requests
import sentry_sdk
import sqlalchemy
from fastapi import HTTPException, Request, Response, RedirectResponse
from loguru import logger
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from auth.repository import AuthRepository
from bot.repository import ThreadModel
from bot.service import BotService
from chat import ChatEngine, ChatEngineSelector
from chat.exceptions import ChatResponseGenerationError

from .reaction_event import Reaction, ReactionEventCreate
from .reaction_event_repository import ReactionEventRepository
from .slack_dto import SlackConfig, WorkspaceData
from .slack_repository import WorkspaceDataRepository


class UnableToRespondToInteraction(Exception):
    pass

class EmptyQuestion(Exception):
    message = "Your question can't be empty"


class MissingChatbot(Exception):
    message = "Whoops. Can't find the chatbot you're looking for."


class SlackAdapter:

    def __init__(
        self,
        app: App,
        engine_selector: ChatEngineSelector,
        bot_service: BotService,
        reaction_event_repository: ReactionEventRepository,
        workspace_data_repository: WorkspaceDataRepository,
        auth_respository: AuthRepository,
        slack_config: SlackConfig
    ) -> None:
        self.app = app
        self.engine_selector = engine_selector
        self.bot_service = bot_service
        self.reaction_event_repository = reaction_event_repository
        self.workspace_data_repository = workspace_data_repository
        self.handler = SlackRequestHandler(self.app)
        self.auth_respository = auth_respository
        self.slack_config = slack_config

    def logger(self):
        return logger.bind(service="SlackAdapter")

    # Function to listen for events on Slack. No need to test this since this is purely dependent on
    # Bolt
    async def handle_events(self, req: Request):  # pragma: no cover
        return await self.handler.handle(req)

    async def oauth_redirect(self, req:Request):
        code = req.query_params.get("code")

        response = self.app.client.oauth_v2_access(
            client_id=self.slack_config.slack_client_id,
            client_secret=self.slack_config.slack_client_secret,
            code=code
        )

        team_id = response["team"]["id"]
        access_token = response["access_token"]
        workspace_data = WorkspaceData(
            team_id=team_id,
            access_token=access_token
        )

        self.workspace_data_repository.create_workspace_data(workspace_data)
        return RedirectResponse(url="/slack/install/success")

    @sentry_sdk.trace
    async def handle_interactions(self, req: Request):
        data = await req.form()

        payload_str = data.get("payload")
        payload = json.loads(payload_str)

        actions = payload["actions"]
        if len(actions) == 1:
            action_id = actions[0]["action_id"]

            sentry_sdk.get_current_scope().set_tag("action_id", action_id)

            self.logger().bind(action_id=action_id).info("handling interaction")
            if action_id == "ask_question":
                channel_id = payload["channel"]["id"]
                user_id = payload["user"]["id"]
                team_id = payload["team"]["id"]
                client = self.create_webclient_based_on_team_id(team_id)
                slug = payload["state"]["values"]["bots"]["select_chatbot"][
                    "selected_option"
                ]["value"]
                question = payload["state"]["values"]["question"]["question"]["value"]

                sentry_sdk.get_current_scope().set_tag("slug", slug)
                sentry_sdk.get_current_scope().set_tag("question", question)

                try:
                    await self.ask_v2(
                        channel_id=channel_id,
                        user_id=user_id,
                        slug=slug,
                        question=question,
                        client=client
                    )
                except (EmptyQuestion, MissingChatbot) as e:
                    raise HTTPException(status_code=400, detail=e.message)

                response_url = payload["response_url"]

                ack_payload = {
                    "response_type": "ephemeral",
                    "text": "",
                    "replace_original": True,
                    "delete_original": True,
                }

                try:
                    res = requests.post(response_url, json=ack_payload)
                    if res.status_code != 200:
                        raise UnableToRespondToInteraction

                except UnableToRespondToInteraction:
                    self.logger().bind(res=res.json()).error(
                        "unable to respond to interaction"
                    )
                except requests.RequestException as e:
                    self.logger().bind(err=e).error("unable to respond to interaction")

        return Response(status_code=200)

    async def load_options(self, req: Request):
        data = await req.form()

        payload_str = data.get("payload")
        payload = json.loads(payload_str)

        action_id = payload["action_id"]

        if action_id == "select_chatbot":
            bots = self.bot_service.get_chatbots(0, 100)
            options = list(
                map(
                    lambda bot: {
                        "text": {
                            "type": "plain_text",
                            "text": f"{bot.name} ({bot.slug})",
                        },
                        "value": bot.slug,
                    },
                    bots,
                )
            )

            return {"options": options}

        return Response(status_code=200)

    def reaction_added(self, event, context):
        reaction = event["reaction"]
        team_id = context["team_id"]
        client = self.create_webclient_based_on_team_id(team_id)

        if reaction == "-1" or reaction == "+1":
            self.handle_rating_reaction(event, client)

        return Response(status_code=200)
    
    def reaction_removed(self, event):
        reaction = event["reaction"]

        # Handle negative reactions
        if reaction == "-1":
            self.remove_reaction(event, Reaction.NEGATIVE)

        return Response(status_code=200)
    
    def handle_rating_reaction(self, event: Dict[str, any], client:WebClient):
        self.logger().info("handle rating reaction")

        # Fetch message data
        res = client.conversations_history(
            channel=event["item"]["channel"],
            oldest=event["item"]["ts"],
            inclusive=True,
            include_all_metadata=True,
            limit=1,
        )
        message = res["messages"][0]

        # Check if message is start of conversation
        if message["thread_ts"] is None or message["ts"] != message["thread_ts"]:
            return

        # Get bot slug and find bot to get bot id
        metadata = message["metadata"]
        if metadata is None:
            return

        metadata_event = metadata["event_type"]
        if metadata_event != "chat-data":
            return

        bot_slug = metadata["event_payload"]["bot_slug"]
        bot = self.bot_service.get_chatbot_by_slug(bot_slug)
        if bot is None:
            return

        # Create reaction event
        reaction_event_create = ReactionEventCreate.from_slack_reaction(
            bot_id=bot.id,
            message=message["text"],
            event=event,
        )

        self.reaction_event_repository.create_reaction_event(reaction_event_create)

    def remove_reaction(self, event: Dict[str, any], reaction:Reaction):
        self.logger().info("handle negative reaction removed")

        source_adapter_message_id=event["item"]["ts"],
        source_adapter_user_id=event["user"],

        self.reaction_event_repository.delete_reaction_event(
                reaction,
                source_adapter_message_id, 
                source_adapter_user_id)

    def send_generated_response(
        self,
        channel: str,
        ts: str,
        engine: ChatEngine,
        question: str,
        access_level: int,
        client:WebClient
    ):
        transaction = sentry_sdk.get_current_scope().transaction
        if transaction is not None:  # pragma: no cover
            trace_id = transaction.trace_id
        else:
            trace_id = ""

        with self.logger().contextualize(trace_id=trace_id):
            self.logger().info("generating response")

            with sentry_sdk.start_transaction(
                trace_id=trace_id,
                op="send_generated_response",
                name=f"{__name__}.{self.send_generated_response.__qualname__}",
            ):
                try:
                    chatbot_response = engine.generate_response(
                        query=question, access_level=access_level
                    )
                    self.logger().info("sending generated response")
                    client.chat_update(
                        channel=channel, ts=ts, text=chatbot_response
                    )

                except ChatResponseGenerationError as e:  # pragma: no cover
                    sentry_sdk.capture_exception(e)
                    self.logger().error(e)
                    client.chat_update(
                        channel=channel,
                        ts=ts,
                        text="Something went wrong when trying to generate your response.",
                    )

    def ask_form(self, _: Request):
        return {
            "blocks": [
                {
                    "type": "section",
                    "block_id": "bots",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Select the chatbot you want to ask*",
                    },
                    "accessory": {
                        "action_id": "select_chatbot",
                        "type": "external_select",
                        "placeholder": {
                            "type": "plain_text",
                            "text": "Select a chatbot",
                        },
                        "min_query_length": 0,
                    },
                },
                {
                    "type": "input",
                    "block_id": "question",
                    "element": {
                        "action_id": "question",
                        "type": "plain_text_input",
                        "multiline": True,
                        "min_length": 1,
                    },
                    "label": {"type": "plain_text", "text": "What is your question?"},
                    "hint": {
                        "type": "plain_text",
                        "text": "e.g. Who's the CEO of our company?",
                    },
                },
                {
                    "type": "actions",
                    "elements": [
                        {
                            "type": "button",
                            "text": {"type": "plain_text", "text": "Ask question"},
                            "style": "primary",
                            "value": "ask_question",
                            "action_id": "ask_question",
                        },
                    ],
                },
            ]
        }

    @sentry_sdk.trace
    async def ask_v2(self, channel_id: str, user_id: str, slug: str, question: str, client:WebClient):
        self.logger().info("answering question")

        if question is None or len(question.strip()) < 1:
            raise EmptyQuestion

        question = f'<@{user_id}> asked: \n\n"{question}" '

        try:
            chatbot = self.bot_service.get_chatbot_by_slug(slug=slug)

            user_info = client.users_info(user=user_id)
            email = user_info["user"]["profile"]["email"]
            user = self.auth_respository.find_user_by_email(email)

            if not user:
                access_level = 1
            else:
                access_level = user.access_level

            if chatbot is None:
                raise MissingChatbot
            
            with self.reaction_event_repository.create_session() as session:
                thread_id = uuid4()
                new_thread = ThreadModel(id=thread_id, bot_id=chatbot.id)
                session.add(new_thread)
                session.commit()

            response = client.chat_postMessage(
                channel=channel_id,
                text=question,
                metadata={
                    "event_type": "chat-data",
                    "event_payload": {
                        "bot_slug": slug,
                    },
                },
            )

            return await self.process_chatbot_request(
                chatbot, question, channel_id, response["ts"], client=client, access_level=access_level
            )

        except SlackApiError as e:
            raise HTTPException(status_code=400, detail=f"Slack API Error: {e}")

    async def ask(self, request: Request):
        data = await request.form()

        channel_id = data.get("channel_id")
        user_id = data.get("user_id")
        parameter = data.get("text", "")
        team_id = data.get("team_id")

        parts = parameter.split(" ", 1)
        if len(parts) == 2:
            bot_slug, question = parts
        else:
            return {
                "text": "Missing parameter in the request.",
            }

        question = f'<@{user_id}> asked: \n\n"{question}" '

        try:
            chatbot = self.bot_service.get_chatbot_by_slug(slug=bot_slug)
            client = self.create_webclient_based_on_team_id(team_id)

            user_info = client.users_info(user=user_id)
            email = user_info["user"]["profile"]["email"]
            user = self.auth_respository.find_user_by_email(email)

            if not user:
                access_level = 1
            else:
                access_level = user.access_level

            if chatbot is None:
                raise MissingChatbot
            
            response = client.chat_postMessage(
                channel=channel_id,
                text=question,
                metadata={
                    "event_type": "chat-data",
                    "event_payload": {
                        "bot_slug": bot_slug,
                    },
                },
            )
            return await self.process_chatbot_request(
                chatbot, question, channel_id, response["ts"], client=client, access_level=access_level
            )

        except SlackApiError as e:
            raise HTTPException(status_code=400, detail=f"Slack API Error: {e}")

    @sentry_sdk.trace
    async def process_chatbot_request(
        self,
        chatbot,
        question,
        channel_id,
        thread_ts,
        client:WebClient,
        access_level=1,
        history=None,
    ):
        try:
            self.logger().info("Processing query using chatbot")
            loading_message = client.chat_postMessage(
                channel=channel_id,
                text=":hourglass_flowing_sand: Processing your request, please wait...",
                thread_ts=thread_ts,
            )

            bot_engine = self.engine_selector.select_engine(engine_type=chatbot.model)

            if history:
                for event in history:
                    role = event.get("role")
                    content = event.get("content")
                    bot_engine.add_chat_history(role, content)

            send_response_thread = threading.Thread(
                target=self.send_generated_response,
                kwargs={
                    "channel": channel_id,
                    "ts": loading_message["ts"],
                    "engine": bot_engine,
                    "question": question,
                    "access_level": access_level,
                    "client": client
                },
            )

            send_response_thread.start()

            return Response(status_code=200)

        except sqlalchemy.exc.DataError as e:  # pragma: no cover
            return {"text": self.MISSING_CHATBOT_ERROR}

        except SlackApiError as e:
            if "thread_ts" in locals():
                try:
                    client.chat_delete(channel=channel_id, ts=thread_ts)
                except SlackApiError as delete_error:
                    raise HTTPException(
                        status_code=400, detail=f"Slack API Error: {delete_error}"
                    )

            raise HTTPException(status_code=400, detail=f"Slack API Error: {e}")

    async def list_bots(self, request: Request):
        data = await request.form()
        channel_id = data.get("channel_id")
        team_id = data.get("team_id")

        bot_responses = self.bot_service.get_chatbots(0, 10)

        response_text = f"{len(bot_responses)} Active Bot(s)"
        response_text += "".join(
            [
                f"\n- {bot_response.name} ({bot_response.slug})"
                for bot_response in bot_responses
            ]
        )

        try:
            client = self.create_webclient_based_on_team_id(team_id)
            client.chat_postMessage(channel=channel_id, text=response_text)
            return Response(status_code=200)
        except SlackApiError as e:
            raise HTTPException(status_code=400, detail=f"Slack API Error : {e}")

    def event_message(self, event):
        if "thread_ts" in event:
            self.event_message_replied(event)

    def event_message_replied(self, event):
        team_id = event["team"]
        client = self.create_webclient_based_on_team_id(team_id)

        parent_message = client.conversations_history(
            channel=event["channel"],
            inclusive=True,
            oldest=event["thread_ts"],
            limit=1,
            include_all_metadata=True,
        )
        parent_user = parent_message["messages"][0]["user"]
        user_id = client.auth_test()["user_id"]

        if (
            parent_user == user_id
            and parent_message["messages"][0].get("metadata") != None
        ):
            self.bot_replied(event, parent_message, client)

    def bot_replied(self, event, parent_message, client:WebClient):
        bot_slug = parent_message["messages"][0]["metadata"]["event_payload"][
            "bot_slug"
        ]
        question = event["text"]
        thread_ts = event["thread_ts"]
        channel_id = event["channel"]
        chatbot = self.bot_service.get_chatbot_by_slug(slug=bot_slug)

        user_id = event["user"]
        user_info = client.users_info(user=user_id)
        email = user_info["user"]["profile"]["email"]
        user = self.auth_respository.find_user_by_email(email)

        if not user:
            access_level = 1
        else:
            access_level = user.access_level

        if chatbot is None:
            raise MissingChatbot

        history = self.get_chat_history(event, client)
        return asyncio.run(
            self.process_chatbot_request(
                chatbot, question, channel_id, thread_ts, client=client, access_level=access_level, history=history
            )
        )

    def get_chat_history(self, event, client:WebClient):
        all_messages = client.conversations_replies(
            channel=event["channel"],
            inclusive=True,
            ts=event["thread_ts"],
            include_all_metadata=True,
        )["messages"]

        result = []
        INTRODUCTION_KEY_WORD = "asked:"

        for i, message in enumerate(all_messages):
            if i == 0:
                question = self.extract_question(message, INTRODUCTION_KEY_WORD)
                if question == None:
                    continue
                if question:
                    result.append({"role": "user", "content": question})
            else:
                self.add_message_to_result(message, result)

        return result

    def extract_question(self, message, key_word):
        if "text" in message and key_word in message["text"]:
            question_start = message["text"].find(key_word) + len(key_word) + 1
            return message["text"][question_start:].strip().strip('"')
        return None

    def add_message_to_result(self, message, result):
        if "text" in message:
            role = "assistant" if "bot_id" in message else "user"
            result.append({"role": role, "content": message["text"]})

    def create_webclient_based_on_team_id(self, team_id: str) -> WebClient:
        workspace_data = self.workspace_data_repository.get_workspace_data_by_team_id(team_id=team_id)
        if workspace_data is None:
            raise ValueError(f"No workspace data found for team_id {team_id}")
        access_token = workspace_data.access_token
        return WebClient(token=access_token)

