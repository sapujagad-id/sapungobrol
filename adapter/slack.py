import sqlalchemy
import threading

from fastapi import Request, Response, HTTPException
from loguru import logger
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from slack_sdk.errors import SlackApiError
from bot.service import BotService
from chat import ChatEngineSelector, ChatEngine
from chat.exceptions import ChatResponseGenerationError


class SlackAdapter:
    def __init__(
        self,
        app: App,
        engine_selector: ChatEngineSelector,
        bot_service: BotService,
    ) -> None:
        self.app = app
        self.engine_selector = engine_selector
        self.bot_service = bot_service
        self.handler = SlackRequestHandler(self.app)
        self.logger = logger.bind(service="SlackAdapter")

    # Function to listen for events on Slack. No need to test this since this is purely dependent on
    # Bolt
    async def handle_events(self, req: Request):  # pragma: no cover
        return await self.handler.handle(req)

    def send_generated_response(
        self, channel: str, ts: str, engine: ChatEngine, question: str
    ):
        try:
            self.logger.info("generating response")

            chatbot_response = engine.generate_response(query=question)

            self.logger.info("sending generated response")

            self.app.client.chat_update(channel=channel, ts=ts, text=chatbot_response)

        except ChatResponseGenerationError as e:  # pragma: no cover
            self.logger.error(e)
            return {
                "text": "Something went wrong when trying to generate your response."
            }

    async def ask(self, request: Request):
        data = await request.form()

        channel_id = data.get("channel_id")
        user_id = data.get("user_id")
        parameter = data.get("text", "")

        parts = parameter.split(" ", 1)
        if len(parts) == 2:
            bot_id, question = parts
        else:
            return {
                "text": "Missing parameter in the request.",
            }

        question = f'<@{user_id}> asked: \n\n"{question}" '

        try:
            chatbot = self.bot_service.get_chatbot_by_id(bot_id=bot_id)

            if chatbot is None:
                return {"text": "Whoops. Can't found the chatbot you're looking for."}

            response = self.app.client.chat_postMessage(
                channel=channel_id, text=question
            )
            thread_ts = response["ts"]

            loading_message = self.app.client.chat_postMessage(
                channel=channel_id,
                text=":hourglass_flowing_sand: Processing your request, please wait...",
                thread_ts=thread_ts,
            )

            bot_engine = self.engine_selector.select_engine(engine_type=chatbot.model)

            send_response_thread = threading.Thread(
                target=self.send_generated_response,
                kwargs={
                    "channel": channel_id,
                    "ts": loading_message["ts"],
                    "engine": bot_engine,
                    "question": question,
                },
            )

            send_response_thread.start()

            return Response(status_code=200)

        except sqlalchemy.exc.DataError as e:  # pragma: no cover
            return {"text": "Whoops. Can't found the chatbot you're looking for"}

        except SlackApiError as e:
            if "thread_ts" in locals():
                try:
                    self.app.client.chat_delete(channel=channel_id, ts=thread_ts)
                except SlackApiError as delete_error:
                    raise HTTPException(
                        status_code=400, detail=f"Slack API Error : {delete_error}"
                    )

            raise HTTPException(status_code=400, detail=f"Slack API Error : {e}")

    async def list_bots(self, request: Request):
        data = await request.form()

        channel_id = data.get("channel_id")

        bot_responses = self.bot_service.get_chatbots(0, 10)

        response_text = f"{len(bot_responses)} Active Bot(s)"
        response_text += "".join(
            [
                f"\n- {bot_response.name} ({bot_response.id})"
                for bot_response in bot_responses
            ]
        )

        try:
            self.app.client.chat_postMessage(channel=channel_id, text=response_text)
            return Response(status_code=200)
        except SlackApiError as e:
            raise HTTPException(status_code=400, detail=f"Slack API Error : {e}")
