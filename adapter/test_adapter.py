import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, HTTPException
from .slack import SlackAdapter
from slack_sdk.errors import SlackApiError
from datetime import datetime
from uuid import uuid4
from bot.bot import BotResponse, MessageAdapter, ModelEngine
from bot.controller import BotController
from bot.helper import relative_time
from chat.chat import ChatOpenAI


class TestAppConfig:

    @pytest.fixture
    def mock_slack_adapter(self):
        with patch('slack_bolt.App') as MockApp:
            mock_app = MockApp()
            mock_chatbot = MagicMock(spec=ChatOpenAI)
            mock_bot_controller = MagicMock(spec=BotController)
            slack_adapter = SlackAdapter(mock_app, mock_chatbot, mock_bot_controller)
            return mock_app, mock_chatbot, mock_bot_controller, slack_adapter

    @pytest.fixture
    def mock_request(self):
        mock_request = MagicMock(spec=Request)
        return mock_request

    async def common_mock_request(self, mock_request, text):
        mock_request.form = AsyncMock(return_value={
            "channel_id": "C12345678",
            "user_id": "U12345678",
            "text": text
        })
        return mock_request

    @pytest.mark.asyncio
    async def test_ask_method(self, mock_slack_adapter, mock_request):
        mock_app, mock_chatbot, _, slack_adapter = mock_slack_adapter

        # Mock Slack API calls
        mock_app.client.chat_postMessage = MagicMock(
            side_effect=[
                {"ts": "1234567890.123456"},
                {"ts": "1234567890.654321"}
            ]
        )
        mock_chatbot.generate_response.return_value = "Chatbot Reply: I'm fine, thank you!"

        mock_request = await self.common_mock_request(mock_request, "12 How are you?")
        response = await slack_adapter.ask(mock_request)

        assert mock_app.client.chat_postMessage.call_count == 2
        mock_app.client.chat_postMessage.assert_any_call(
            channel="C12345678",
            text="<@U12345678> asked: \n\n\"How are you?\" "
        )
        mock_app.client.chat_update.assert_called_once_with(
            channel="C12345678",
            ts="1234567890.654321",
            text="Chatbot Reply: I'm fine, thank you!"
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_missing_parameter_incomplete_text(self, mock_slack_adapter, mock_request):
        mock_app, _, _, slack_adapter = mock_slack_adapter

        mock_request = await self.common_mock_request(mock_request, "12")

        with pytest.raises(HTTPException) as excinfo:
            await slack_adapter.ask(mock_request)
        assert excinfo.value.status_code == 400
        assert excinfo.value.detail == "Missing parameter in the request."
        mock_app.client.chat_postMessage.assert_not_called()

    @pytest.mark.asyncio
    async def test_chat_post_message_failure(self, mock_slack_adapter, mock_request):
        mock_app, _, _, slack_adapter = mock_slack_adapter

        mock_app.client.chat_postMessage = MagicMock(
            side_effect=[
                {"ts": "1234567890.123456"},
                SlackApiError("Error posting message", response={})
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
            channel="C12345678",
            ts="1234567890.123456"
        )

    @pytest.mark.asyncio
    async def test_chat_post_message_and_delete_failure(self, mock_slack_adapter, mock_request):
        mock_app, _, _, slack_adapter = mock_slack_adapter

        mock_app.client.chat_postMessage = MagicMock(
            side_effect=[
                {"ts": "1234567890.123456"},
                SlackApiError("Error posting message", response={})
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
            channel="C12345678",
            ts="1234567890.123456"
        )

    @pytest.mark.asyncio
    async def test_success_integration_ask_chat(self, mock_slack_adapter, mock_request):
        mock_app, mock_chatbot, _, slack_adapter = mock_slack_adapter

        mock_app.client.users_info = MagicMock(
            return_value={"user": {"profile": {"display_name": "Test User"}}}
        )
        mock_app.client.chat_postMessage = MagicMock(return_value={"ts": "1234567890.123456"})
        mock_chatbot.generate_response.return_value = "Chatbot Response: Hello!"

        mock_request = await self.common_mock_request(mock_request, "12 How is the weather?")

        await slack_adapter.ask(mock_request)

        mock_chatbot.generate_response.assert_called_once_with(query="<@U12345678> asked: \n\n\"How is the weather?\" ")
        assert mock_app.client.chat_postMessage.call_count == 2
        mock_app.client.chat_postMessage.assert_any_call(
            channel="C12345678",
            text="<@U12345678> asked: \n\n\"How is the weather?\" "
        )
        mock_app.client.chat_update.assert_called_once_with(
            channel="C12345678",
            ts="1234567890.123456",
            text="Chatbot Response: Hello!"
        )

    @pytest.mark.asyncio
    @patch('chat.chat.ChatOpenAI.generate_response')
    async def test_failing_integration_ask_chat_empty_query(self, mock_generate_response, mock_slack_adapter, mock_request):
        mock_app, _, _, slack_adapter = mock_slack_adapter

        mock_generate_response.return_value = ""

        mock_request = await self.common_mock_request(mock_request, "")

        with pytest.raises(HTTPException) as excinfo:
            await slack_adapter.ask(mock_request)
        assert excinfo.value.status_code == 400
        assert excinfo.value.detail == "Missing parameter in the request."
        mock_generate_response.assert_not_called()
        mock_app.client.chat_postMessage.assert_not_called()

    @pytest.mark.asyncio
    async def test_edge_case_no_context_in_chat(self, mock_slack_adapter, mock_request):
        mock_app, mock_chatbot, _, slack_adapter = mock_slack_adapter

        mock_app.client.users_info = MagicMock(
            return_value={"user": {"profile": {"display_name": "Test User"}}}
        )
        mock_app.client.chat_postMessage = MagicMock(return_value={"ts": "1234567890.123456"})
        mock_chatbot.generate_response.return_value = "I'm not sure how to answer that."

        mock_request = await self.common_mock_request(mock_request, "12 Explain quantum computing")

        await slack_adapter.ask(mock_request)

        mock_chatbot.generate_response.assert_called_once_with(query="<@U12345678> asked: \n\n\"Explain quantum computing\" ")
        assert mock_app.client.chat_postMessage.call_count == 2
        mock_app.client.chat_postMessage.assert_any_call(
            channel="C12345678",
            text="<@U12345678> asked: \n\n\"Explain quantum computing\" "
        )
        mock_app.client.chat_update.assert_called_once_with(
            channel="C12345678",
            ts="1234567890.123456",
            text="I'm not sure how to answer that."
        )
    
    @pytest.mark.asyncio
    async def test_list_bots_method(self, mock_slack_adapter, mock_request):
        mock_app, _, mock_bot_controller, slack_adapter = mock_slack_adapter
        
        mock_app.client.chat_postMessage = MagicMock(
            side_effect=[
                {"ts": "1234567890.123456"},
            ]
        )
        
        first_bot_id = uuid4()
        second_bot_id = uuid4()
        
        mock_bot_controller.fetch_chatbots = MagicMock(
            return_value=[
                BotResponse(
                    id = first_bot_id,
                    name = "Bot A",
                    system_prompt = "prompt A here",
                    model = ModelEngine.OPENAI,
                    adapter = MessageAdapter.SLACK,
                    created_at = datetime.fromisocalendar(2024, 1, 1),
                    updated_at = datetime.fromisocalendar(2024, 1, 1),
                    updated_at_relative = relative_time(datetime.fromisocalendar(2024, 1, 1)),
                ),
                BotResponse(
                    id = second_bot_id,
                    name = "Bot B",
                    system_prompt = "a much longer prompt B here",
                    model = ModelEngine.OPENAI,
                    adapter = MessageAdapter.SLACK,
                    created_at = datetime.now(),
                    updated_at = datetime.now(),
                    updated_at_relative = relative_time(datetime.now()),
                )
            ]
        )
        
        mock_request = await self.common_mock_request(mock_request, "")
        
        response = await slack_adapter.list_bots(mock_request)

        assert mock_app.client.chat_postMessage.call_count == 1
        
        mock_app.client.chat_postMessage.assert_any_call(
            channel="C12345678",
            text=f"2 Active Bot(s)\n- Bot A ({first_bot_id})\n- Bot B ({second_bot_id})"
        )
        
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_list_bots_method_chat_postMessage_failure(self, mock_slack_adapter, mock_request):
        mock_app, _, mock_bot_controller, slack_adapter = mock_slack_adapter
        
        mock_app.client.chat_postMessage = MagicMock(
            side_effect=[
                SlackApiError("Error posting message", response={}),
            ]
        )
        
        first_bot_id = uuid4()
        second_bot_id = uuid4()
        
        mock_bot_controller.fetch_chatbots = MagicMock(
            return_value=[
                BotResponse(
                    id = first_bot_id,
                    name = "Bot A",
                    system_prompt = "prompt A here",
                    model = ModelEngine.OPENAI,
                    adapter = MessageAdapter.SLACK,
                    created_at = datetime.fromisocalendar(2024, 1, 1),
                    updated_at = datetime.fromisocalendar(2024, 1, 1),
                    updated_at_relative = relative_time(datetime.fromisocalendar(2024, 1, 1)),
                ),
                BotResponse(
                    id = second_bot_id,
                    name = "Bot B",
                    system_prompt = "a much longer prompt B here",
                    model = ModelEngine.OPENAI,
                    adapter = MessageAdapter.SLACK,
                    created_at = datetime.now(),
                    updated_at = datetime.now(),
                    updated_at_relative = relative_time(datetime.now()),
                )
            ]
        )
        
        mock_request = await self.common_mock_request(mock_request, "")

        with pytest.raises(HTTPException) as excinfo:
            await slack_adapter.list_bots(mock_request)
        assert excinfo.value.status_code == 400
        assert "Slack API Error" in excinfo.value.detail
        assert mock_app.client.chat_postMessage.call_count == 1