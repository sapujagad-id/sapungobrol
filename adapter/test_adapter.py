import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, HTTPException
from .slack import SlackAdapter
from slack_sdk.errors import SlackApiError


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
                        {"ok": True} 
                    ]
                )
                
                mock_bot_controller.fetch_chatbots = MagicMock(
                    return_value=[
                        [
                            {
                                'id': 'bot1',
                                'name': 'Bot A',
                                'system_prompt': 'Prompt A',
                                'model': 'OpenAI',
                                'adapter': 'Slack',
                                'updated_at': '2024-10-04T00:00:00Z'
                            },
                            {
                                'id': 'bot2',
                                'name': 'Bot B',
                                'system_prompt': 'Prompt B',
                                'model': 'OpenAI',
                                'adapter': 'Slack',
                                'updated_at': '2024-10-04T00:00:00Z'
                            }
                        ]
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
                    text="2 Active Bots:\n- Bot A\n- Bot B"
                )
                
                assert response.status_code == 200
                