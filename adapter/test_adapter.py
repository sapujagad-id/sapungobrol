import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, HTTPException
from .slack import SlackAdapter
from slack_sdk.errors import SlackApiError
from datetime import datetime
from uuid import uuid4
from bot.bot import BotResponse, MessageAdapter, ModelEngine
from bot.helper import relative_time


class TestAppConfig:

    @pytest.mark.asyncio
    async def test_ask_method(self):
        with patch('slack_bolt.App') as MockApp:
            with patch('bot.BotControllerV1') as MockBotController:
                mock_app = MockApp()
                mock_bot_controller = MockBotController()
                
                mock_app.client.chat_postMessage = MagicMock(
                    side_effect=[
                        {"ts": "1234567890.123456"},  
                        {"ok": True} 
                    ]
                )

                slack_adapter = SlackAdapter(mock_app, mock_bot_controller)

                mock_request = MagicMock(spec=Request)
                mock_request.form = AsyncMock(return_value={
                    "channel_id": "C12345678",
                    "user_id": "U12345678",
                    "text": "12 How are you?"
                })

                response = await slack_adapter.ask(mock_request)

                assert mock_app.client.chat_postMessage.call_count == 2

                mock_app.client.chat_postMessage.assert_any_call(
                    channel="C12345678",
                    text="How are you? \n\n<@U12345678>"
                )

                mock_app.client.chat_postMessage.assert_any_call(
                    channel="C12345678",
                    text="This is a reply to the message.",
                    thread_ts="1234567890.123456"
                )

                assert response.status_code == 200

    @pytest.mark.asyncio 
    async def test_missing_parameter_incomplete_text(self):
        with patch('slack_bolt.App') as MockApp:
            with patch('bot.BotControllerV1') as MockBotController:
                mock_app = MockApp()
                mock_bot_controller = MockBotController()
                mock_app.client.chat_postMessage = MagicMock()

                slack_adapter = SlackAdapter(mock_app, mock_bot_controller)

                mock_request = MagicMock(spec=Request)
                mock_request.form = AsyncMock(return_value={
                    "channel_id": "C12345678",
                    "user_id": "U12345678",
                    "text": "12"
                })

                with pytest.raises(HTTPException) as excinfo:
                    await slack_adapter.ask(mock_request)
                
                assert excinfo.value.status_code == 400
                assert excinfo.value.detail == "Missing parameter in the request."

                mock_app.client.chat_postMessage.assert_not_called()

    @pytest.mark.asyncio
    async def test_chat_post_message_failure(self):
        with patch('slack_bolt.App') as MockApp:
            with patch('bot.BotControllerV1') as MockBotController:
                mock_app = MockApp()
                mock_bot_controller = MockBotController()
                
                mock_app.client.chat_postMessage = MagicMock(
                    side_effect=[
                        {"ts": "1234567890.123456"},
                        SlackApiError("Error posting message", response={})
                    ]
                )
                mock_app.client.chat_delete = MagicMock()  

                slack_adapter = SlackAdapter(mock_app, mock_bot_controller)

                mock_request = MagicMock(spec=Request)
                mock_request.form = AsyncMock(return_value={
                    "channel_id": "C12345678",
                    "user_id": "U12345678",
                    "text": "12 How are you?"
                })
                
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
    async def test_chat_post_message_and_delete_failure(self):
        with patch('slack_bolt.App') as MockApp:
            with patch('bot.BotControllerV1') as MockBotController:
                mock_app = MockApp()
                mock_bot_controller = MockBotController()
                
                mock_app.client.chat_postMessage = MagicMock(
                    side_effect=[
                        {"ts": "1234567890.123456"},
                        SlackApiError("Error posting message", response={})
                    ]
                )
                mock_app.client.chat_delete = MagicMock(
                    side_effect=SlackApiError("Error delete message", response={})

                )
                slack_adapter = SlackAdapter(mock_app, mock_bot_controller)

                mock_request = MagicMock(spec=Request)
                mock_request.form = AsyncMock(return_value={
                    "channel_id": "C12345678",
                    "user_id": "U12345678",
                    "text": "12 How are you?"
                })

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
    async def test_listbots_method(self):
        with patch('slack_bolt.App') as MockApp:
            with patch('bot.BotControllerV1') as MockBotController:
                mock_app = MockApp()
                mock_bot_controller = MockBotController()
                
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
                
                slack_adapter = SlackAdapter(mock_app, mock_bot_controller)

                mock_request = MagicMock(spec=Request)
                mock_request.form = AsyncMock(return_value={
                    "channel_id": "C12345678",
                    "user_id": "U12345678",
                    "text": ""
                })
                
                response = await slack_adapter.list_bots(mock_request)

                assert mock_app.client.chat_postMessage.call_count == 1
                
                mock_app.client.chat_postMessage.assert_any_call(
                    channel="C12345678",
                    text=f"2 Active Bots:\n- Bot A ({first_bot_id})\n- Bot B ({second_bot_id})"
                )
                
                assert response.status_code == 200
                