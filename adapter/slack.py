import sqlalchemy
import threading
import asyncio
import json
import requests

from typing import Any, Dict
from fastapi import Request, Response, HTTPException
from loguru import logger
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from slack_sdk.errors import SlackApiError
from auth.repository import AuthRepository
from bot.service import BotService
from chat import ChatEngineSelector, ChatEngine
from chat.exceptions import ChatResponseGenerationError
from .reaction_event import ReactionEventCreate
from .reaction_event_repository import ReactionEventRepository


class UnableToRespondToInteraction(Exception):
    pass


class EmptyQuestion(Exception):
    message = "Your question can't be empty"


class MissingChatbot(Exception):
    message = "Whoops. Can't find the chatbot you're looking for."


class SlackAdapter:
    MISSING_CHATBOT_ERROR = "Whoops. Can't find the chatbot you're looking for."

    def __init__(
        self,
        app: App,
        engine_selector: ChatEngineSelector,
        bot_service: BotService,
        reaction_event_repository: ReactionEventRepository,
        auth_respository: AuthRepository,
    ) -> None:
        self.app = app
        self.engine_selector = engine_selector
        self.bot_service = bot_service
        self.reaction_event_repository = reaction_event_repository
        self.handler = SlackRequestHandler(self.app)
        self.app_user_id = self.app.client.auth_test()["user_id"]
        self.auth_respository = auth_respository

    def logger(self):
        return logger.bind(service="SlackAdapter")

    # Function to listen for events on Slack. No need to test this since this is purely dependent on
    # Bolt
    async def handle_events(self, req: Request):  # pragma: no cover
        return await self.handler.handle(req)

    async def handle_interactions(self, req: Request):
        data = await req.form()

        payload_str = data.get("payload")
        payload = json.loads(payload_str)

        actions = payload["actions"]
        if len(actions) == 1:
            action_id = actions[0]["action_id"]

            self.logger().bind(action_id=action_id).info("handling interaction")
            if action_id == "ask_question":
                channel_id = payload["channel"]["id"]
                user_id = payload["user"]["id"]
                slug = payload["state"]["values"]["bots"]["select_chatbot"][
                    "selected_option"
                ]["value"]
                question = payload["state"]["values"]["question"]["question"]["value"]

                try:
                    await self.ask_v2(
                        channel_id=channel_id,
                        user_id=user_id,
                        slug=slug,
                        question=question,
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

    def reaction_added(self, event: Dict[str, any]):
        reaction = event["reaction"]

        # Handle negative reactions
        if reaction == "-1":
            self.negative_reaction(event=event)

        return Response(status_code=200)

    def negative_reaction(self, event: Dict[str, any]):
        self.logger().info("handle negative reaction")

        # Fetch message data
        res = self.app.client.conversations_history(
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

    def send_generated_response(
        self, channel: str, ts: str, engine: ChatEngine, question: str, access_level: int
    ):
        try:
            self.logger().info("generating response")

            chatbot_response = engine.generate_response(query=question, access_level=access_level)

            self.logger().info("sending generated response")

            self.app.client.chat_update(channel=channel, ts=ts, text=chatbot_response)

        except ChatResponseGenerationError as e:  # pragma: no cover
            self.logger().error(e)
            self.app.client.chat_update(
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

    async def ask_v2(self, channel_id: str, user_id: str, slug: str, question: str):
        self.logger().info("answering question")

        if question is None or len(question.strip()) < 1:
            raise EmptyQuestion

        question = f'<@{user_id}> asked: \n\n"{question}" '

        try:
            chatbot = self.bot_service.get_chatbot_by_slug(slug=slug)

            user_info = self.app.client.users_info(user=user_id)
            email = user_info["user"]["profile"]["email"]
            user = self.auth_respository.find_user_by_email(email)
            
            if not user:
                access_level = 1
            else:
                access_level = user.access_level

            if chatbot is None:
                raise MissingChatbot

            response = self.app.client.chat_postMessage(
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
                chatbot, question, channel_id, response["ts"], access_level
            )

        except SlackApiError as e:
            raise HTTPException(status_code=400, detail=f"Slack API Error: {e}")

    async def ask(self, request: Request):
        data = await request.form()

        channel_id = data.get("channel_id")
        user_id = data.get("user_id")
        parameter = data.get("text", "")

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

            if chatbot is None:
                return {"text": self.MISSING_CHATBOT_ERROR}

            response = self.app.client.chat_postMessage(
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
                chatbot, question, channel_id, response["ts"]
            )

        except SlackApiError as e:
            raise HTTPException(status_code=400, detail=f"Slack API Error: {e}")

    async def process_chatbot_request(
        self, chatbot, question, channel_id, thread_ts, access_level, history=None,
    ):
        try:
            self.logger().info("Processing query using chatbot")
            loading_message = self.app.client.chat_postMessage(
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
                    "access_level": access_level
                },
            )

            send_response_thread.start()

            return Response(status_code=200)

        except sqlalchemy.exc.DataError as e:  # pragma: no cover
            return {"text": self.MISSING_CHATBOT_ERROR}

        except SlackApiError as e:
            if "thread_ts" in locals():
                try:
                    self.app.client.chat_delete(channel=channel_id, ts=thread_ts)
                except SlackApiError as delete_error:
                    raise HTTPException(
                        status_code=400, detail=f"Slack API Error: {delete_error}"
                    )

            raise HTTPException(status_code=400, detail=f"Slack API Error: {e}")

    async def list_bots(self, request: Request):
        data = await request.form()

        channel_id = data.get("channel_id")

        bot_responses = self.bot_service.get_chatbots(0, 10)

        response_text = f"{len(bot_responses)} Active Bot(s)"
        response_text += "".join(
            [
                f"\n- {bot_response.name} ({bot_response.slug})"
                for bot_response in bot_responses
            ]
        )

        try:
            self.app.client.chat_postMessage(channel=channel_id, text=response_text)
            return Response(status_code=200)
        except SlackApiError as e:
            raise HTTPException(status_code=400, detail=f"Slack API Error : {e}")

    def event_message(self, event):
        if "thread_ts" in event:
            self.event_message_replied(event)

    def event_message_replied(self, event):
        parent_message = self.app.client.conversations_history(
            channel=event["channel"],
            inclusive=True,
            oldest=event["thread_ts"],
            limit=1,
            include_all_metadata=True,
        )

        parent_user = parent_message["messages"][0]["user"]

        if (
            parent_user == self.app_user_id
            and parent_message["messages"][0].get("metadata") != None
        ):
            self.bot_replied(event, parent_message)

    def bot_replied(self, event, parent_message):
        bot_slug = parent_message["messages"][0]["metadata"]["event_payload"][
            "bot_slug"
        ]
        question = event["text"]
        thread_ts = event["thread_ts"]
        channel_id = event["channel"]
        chatbot = self.bot_service.get_chatbot_by_slug(slug=bot_slug)

        if chatbot is None:
            return {"text": self.MISSING_CHATBOT_ERROR}

        history = self.get_chat_history(event)
        return asyncio.run(
            self.process_chatbot_request(
                chatbot, question, channel_id, thread_ts, history
            )
        )

    def get_chat_history(self, event):
        all_messages = self.app.client.conversations_replies(
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
