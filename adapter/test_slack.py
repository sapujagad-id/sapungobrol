import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, HTTPException
from .slack import SlackAdapter
from slack_sdk.errors import SlackApiError
from datetime import datetime
from uuid import uuid4
from bot.bot import BotResponse, MessageAdapter, ModelEngine
from bot.service import BotService
from bot.helper import relative_time
from chat import ChatEngineSelector, ChatOpenAI
from chat.exceptions import ChatResponseGenerationError


class TestSlackAdapter:
    @pytest.fixture
    def mock_slack_adapter(self):
        with patch("slack_bolt.App") as MockApp:
            mock_app = MockApp()
            mock_engine_selector = MagicMock(spec=ChatEngineSelector)
            mock_engine_selector.select_engine = MagicMock(return_value=ChatOpenAI())
            mock_chatbot = mock_engine_selector.select_engine()
            mock_bot_service = MagicMock(spec=BotService)
            slack_adapter = SlackAdapter(
                mock_app, mock_engine_selector, mock_bot_service
            )
            return mock_app, mock_chatbot, mock_bot_service, slack_adapter

    @pytest.fixture
    def mock_request(self):
        return MagicMock(spec=Request)

    @pytest.fixture
    def mock_bot_response_list(self):
        first_bot_id = uuid4()
        second_bot_id = uuid4()

        mock_bot_response_list = MagicMock(
            return_value=[
                BotResponse(
                    id=first_bot_id,
                    name="Bot A",
                    system_prompt="prompt A here",
                    slug="bot-a",
                    model=ModelEngine.OPENAI,
                    adapter=MessageAdapter.SLACK,
                    created_at=datetime.fromisocalendar(2024, 1, 1),
                    updated_at=datetime.fromisocalendar(2024, 1, 1),
                    updated_at_relative=relative_time(
                        datetime.fromisocalendar(2024, 1, 1)
                    ),
                ),
                BotResponse(
                    id=second_bot_id,
                    name="Bot B",
                    system_prompt="a much longer prompt B here",
                    slug="bot-b",
                    model=ModelEngine.OPENAI,
                    adapter=MessageAdapter.SLACK,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    updated_at_relative=relative_time(datetime.now()),
                ),
            ]
        )

        return first_bot_id, second_bot_id, mock_bot_response_list

    async def common_mock_request(self, mock_request, text):
        mock_request.form = AsyncMock(
            return_value={
                "channel_id": "C12345678",
                "user_id": "U12345678",
                "text": text,
            }
        )
        return mock_request

    @pytest.mark.asyncio
    async def test_send_generated_response(self, mock_slack_adapter):
        mock_app, mock_chatbot, _, slack_adapter = mock_slack_adapter

        # Mock Slack API calls
        mock_app.client.chat_postMessage = MagicMock(
            side_effect=[{"ts": "1234567890.123456"}, {"ts": "1234567890.654321"}]
        )
        mock_chatbot.generate_response = MagicMock(
            return_value="Chatbot Reply: I'm fine, thank you!"
        )

        slack_adapter.send_generated_response(
            "C12345678", "1234567890.654321", mock_chatbot, "How are you?"
        )
        mock_app.client.chat_update.assert_called_once_with(
            channel="C12345678",
            ts="1234567890.654321",
            text="Chatbot Reply: I'm fine, thank you!",
        )

    @pytest.mark.asyncio
    async def test_send_generated_response_generation_error(self, mock_slack_adapter):
        mock_app, mock_chatbot, _, slack_adapter = mock_slack_adapter

        # Mock Slack API calls
        mock_app.client.chat_postMessage = MagicMock(
            side_effect=[{"ts": "1234567890.123456"}, {"ts": "1234567890.654321"}]
        )
        mock_chatbot.generate_response = MagicMock(
            side_effect=ChatResponseGenerationError
        )

        response = slack_adapter.send_generated_response(
            "C12345678", "1234567890.654321", mock_chatbot, "How are you?"
        )

        mock_app.client.chat_update.assert_called_once_with(
            channel="C12345678",
            ts="1234567890.654321",
            text="Something went wrong when trying to generate your response.",
        )

    @pytest.mark.asyncio
    async def test_ask_method(self, mock_slack_adapter, mock_request):
        mock_app, mock_chatbot, _, slack_adapter = mock_slack_adapter

        # Mock Slack API calls
        mock_app.client.chat_postMessage = MagicMock(
            side_effect=[{"ts": "1234567890.123456"}, {"ts": "1234567890.654321"}]
        )
        mock_chatbot.generate_response = MagicMock(
            return_value="Chatbot Reply: I'm fine, thank you!"
        )

        mock_request = await self.common_mock_request(mock_request, "12 How are you?")
        response = await slack_adapter.ask(mock_request)

        assert mock_app.client.chat_postMessage.call_count == 2
        mock_app.client.chat_postMessage.assert_any_call(
            channel="C12345678", text='<@U12345678> asked: \n\n"How are you?" '
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_missing_parameter_incomplete_text(
        self, mock_slack_adapter, mock_request
    ):
        mock_app, _, _, slack_adapter = mock_slack_adapter

        mock_request = await self.common_mock_request(mock_request, "12")

        res = await slack_adapter.ask(mock_request)
        assert res["text"] == "Missing parameter in the request."
        mock_app.client.chat_postMessage.assert_not_called()

    @pytest.mark.asyncio
    async def test_chat_post_message_failure(self, mock_slack_adapter, mock_request):
        mock_app, _, _, slack_adapter = mock_slack_adapter

        mock_app.client.chat_postMessage = MagicMock(
            side_effect=[
                {"ts": "1234567890.123456"},
                SlackApiError("Error posting message", response={}),
            ]
        )
        mock_app.client.chat_delete = MagicMock()

        mock_request = await self.common_mock_request(mock_request, "12 How are you?")

        with pytest.raises(HTTPException) as excinfo:
            await slack_adapter.ask(mock_request)
        assert excinfo.value.status_code == 400
        assert "Slack API Error" in excinfo.value.detail
        assert mock_app.client.chat_postMessage.call_count == 2
        mock_app.client.chat_delete.assert_called_once_with(
            channel="C12345678", ts="1234567890.123456"
        )

    @pytest.mark.asyncio
    async def test_chat_post_message_and_delete_failure(
        self, mock_slack_adapter, mock_request
    ):
        mock_app, _, _, slack_adapter = mock_slack_adapter

        mock_app.client.chat_postMessage = MagicMock(
            side_effect=[
                {"ts": "1234567890.123456"},
                SlackApiError("Error posting message", response={}),
            ]
        )
        mock_app.client.chat_delete = MagicMock(
            side_effect=SlackApiError("Error delete message", response={})
        )

        mock_request = await self.common_mock_request(mock_request, "12 How are you?")

        with pytest.raises(HTTPException) as excinfo:
            await slack_adapter.ask(mock_request)
        assert excinfo.value.status_code == 400
        assert "Slack API Error" in excinfo.value.detail
        assert mock_app.client.chat_postMessage.call_count == 2
        mock_app.client.chat_delete.assert_called_once_with(
            channel="C12345678", ts="1234567890.123456"
        )

    @pytest.mark.asyncio
    async def test_success_integration_ask_chat(self, mock_slack_adapter, mock_request):
        mock_app, mock_chatbot, _, slack_adapter = mock_slack_adapter

        mock_app.client.users_info = MagicMock(
            return_value={"user": {"profile": {"display_name": "Test User"}}}
        )
        mock_app.client.chat_postMessage = MagicMock(
            return_value={"ts": "1234567890.123456"}
        )
        mock_chatbot.generate_response = MagicMock(
            return_value="Chatbot Response: Hello!"
        )

        mock_request = await self.common_mock_request(
            mock_request, "12 How is the weather?"
        )

        await slack_adapter.ask(mock_request)

        time.sleep(1)

        mock_chatbot.generate_response.assert_called_once_with(
            query='<@U12345678> asked: \n\n"How is the weather?" '
        )
        assert mock_app.client.chat_postMessage.call_count == 2
        mock_app.client.chat_postMessage.assert_any_call(
            channel="C12345678", text='<@U12345678> asked: \n\n"How is the weather?" '
        )
        mock_app.client.chat_update.assert_called_once_with(
            channel="C12345678", ts="1234567890.123456", text="Chatbot Response: Hello!"
        )

    @pytest.mark.asyncio
    async def test_failing_integration_ask_chat_empty_query(
        self, mock_slack_adapter, mock_request
    ):
        mock_app, mock_chatbot, _, slack_adapter = mock_slack_adapter

        mock_chatbot.generate_response = MagicMock(return_value="")

        mock_request = await self.common_mock_request(mock_request, "")

        res = await slack_adapter.ask(mock_request)
        assert res["text"] == "Missing parameter in the request."
        mock_chatbot.generate_response.assert_not_called()
        mock_app.client.chat_postMessage.assert_not_called()

    @pytest.mark.asyncio
    async def test_edge_case_no_context_in_chat(self, mock_slack_adapter, mock_request):
        mock_app, mock_chatbot, _, slack_adapter = mock_slack_adapter

        mock_app.client.users_info = MagicMock(
            return_value={"user": {"profile": {"display_name": "Test User"}}}
        )
        mock_app.client.chat_postMessage = MagicMock(
            return_value={"ts": "1234567890.123456"}
        )
        mock_chatbot.generate_response = MagicMock(
            return_value="I'm not sure how to answer that."
        )

        mock_request = await self.common_mock_request(
            mock_request, "12 Explain quantum computing"
        )

        await slack_adapter.ask(mock_request)

        time.sleep(1)

        mock_chatbot.generate_response.assert_called_once_with(
            query='<@U12345678> asked: \n\n"Explain quantum computing" '
        )
        assert mock_app.client.chat_postMessage.call_count == 2
        mock_app.client.chat_postMessage.assert_any_call(
            channel="C12345678",
            text='<@U12345678> asked: \n\n"Explain quantum computing" ',
        )
        mock_app.client.chat_update.assert_called_once_with(
            channel="C12345678",
            ts="1234567890.123456",
            text="I'm not sure how to answer that.",
        )

    @pytest.mark.asyncio
    async def test_ask_no_bots(self, mock_slack_adapter, mock_request):
        mock_app, _, mock_bot_service, slack_adapter = mock_slack_adapter

        mock_app.client.chat_postMessage = MagicMock(
            side_effect=[
                {"ts": "1234567890.123456"},
            ]
        )

        mock_bot_service.get_chatbot_by_id = MagicMock(return_value=None)

        req = await self.common_mock_request(
            mock_request, "12 Explain quantum computing"
        )

        res = await slack_adapter.ask(req)
        assert res["text"] == "Whoops. Can't found the chatbot you're looking for."

    @pytest.mark.asyncio
    async def test_list_bots_method(
        self, mock_slack_adapter, mock_request, mock_bot_response_list
    ):
        mock_app, _, mock_bot_service, slack_adapter = mock_slack_adapter

        mock_app.client.chat_postMessage = MagicMock(
            side_effect=[
                {"ts": "1234567890.123456"},
            ]
        )

        first_bot_id, second_bot_id, mock_bot_service.get_chatbots = (
            mock_bot_response_list
        )

        mock_request = await self.common_mock_request(mock_request, "")

        response = await slack_adapter.list_bots(mock_request)

        assert mock_app.client.chat_postMessage.call_count == 1

        mock_app.client.chat_postMessage.assert_any_call(
            channel="C12345678",
            text=f"2 Active Bot(s)\n- Bot A ({first_bot_id})\n- Bot B ({second_bot_id})",
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_bots_method_post_message_failure(
        self, mock_slack_adapter, mock_request, mock_bot_response_list
    ):
        mock_app, _, mock_bot_service, slack_adapter = mock_slack_adapter

        mock_app.client.chat_postMessage = MagicMock(
            side_effect=[
                SlackApiError("Error posting message", response={}),
            ]
        )

        _, _, mock_bot_service.get_chatbots = mock_bot_response_list

        mock_request = await self.common_mock_request(mock_request, "")

        with pytest.raises(HTTPException) as excinfo:
            await slack_adapter.list_bots(mock_request)
        assert excinfo.value.status_code == 400
        assert "Slack API Error" in excinfo.value.detail
        assert mock_app.client.chat_postMessage.call_count == 1
    
    def test_event_message_without_thread(self, mock_slack_adapter):
        _, _, _, slack_adapter = mock_slack_adapter
        
        mock_say = MagicMock()

        event = {
            "type": "message",
            "channel": "C123ABC456",
            "user": "U123ABC456",
            "text": "Hello world",
            "ts": "1355517523.000005"
        }

        slack_adapter.event_message_replied = MagicMock()

        slack_adapter.event_message(event, mock_say)

        slack_adapter.event_message_replied.assert_not_called()
        
    def test_event_message_with_thread_wrong_user(self, mock_slack_adapter):
        _, _, _, slack_adapter = mock_slack_adapter
        
        mock_say = MagicMock()

        event = {"thread_ts": "1355517523.000005", "channel": "C123ABC456"}

        slack_adapter.app.client.conversations_history.return_value = {
            "messages": [
                {"user": "U123NONBOT", "text": '<@U07N64EUJ8Y> asked:\n\n"hello"'}
            ]
        }

        slack_adapter.bot_replied = MagicMock()

        slack_adapter.event_message(event, mock_say)

        slack_adapter.bot_replied.assert_not_called()

    def test_event_message_with_thread_wrong_parent_message(self, mock_slack_adapter):
        _, _, _, slack_adapter = mock_slack_adapter
        
        mock_say = MagicMock()

        event = {"thread_ts": "1355517523.000005", "channel": "C123ABC456"}

        slack_adapter.app.client.conversations_history.return_value = {
            "messages": [
                {"user": slack_adapter.app_user_id, "text": "This is a random message"}
            ]
        }

        slack_adapter.bot_replied = MagicMock()

        slack_adapter.event_message(event, mock_say)

        slack_adapter.bot_replied.assert_not_called()

    def test_event_message_with_thread_bot_replied(self, mock_slack_adapter):
        _, _, _, slack_adapter = mock_slack_adapter
        
        mock_say = MagicMock()

        event = {"thread_ts": "1355517523.000005", "channel": "C123ABC456"}

        slack_adapter.app.client.conversations_history.return_value = {
            "messages": [
                {"user": slack_adapter.app_user_id, "text": '<@U07N64EUJ8Y> asked:\n\n"hello"'}
            ]
        }

        slack_adapter.event_message(event, mock_say)

        mock_say.assert_called_once_with("To be implemented", thread_ts="1355517523.000005")
