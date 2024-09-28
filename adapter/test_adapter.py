import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, HTTPException
from slack_bolt import App
from .slack import SlackAdapter


class TestAppConfig:
    
    @pytest.mark.asyncio
    async def test_ask_method(self):
        with patch('slack_bolt.App') as MockApp:
            mock_app = MockApp()
            mock_app.client.users_info = MagicMock(
                return_value={"user": {"profile": {"display_name": "Test User"}}}
            )
            mock_app.client.chat_postMessage = MagicMock()

            slack_adapter = SlackAdapter(mock_app)

            mock_request = MagicMock(spec=Request)
            mock_request.form = AsyncMock(return_value={
                "channel_id": "C12345678",
                "user_id": "U12345678",
                "text": "12 How are you?"
            })

            await slack_adapter.ask(mock_request)

            mock_app.client.users_info.assert_called_once_with(user="U12345678")
            mock_app.client.chat_postMessage.assert_called_once_with(
                channel="C12345678",
                text="How are you? \n\n-Test User"
            )
           
    @pytest.mark.asyncio 
    async def test_missing_parameter(self):
        with patch('slack_bolt.App') as MockApp:
            mock_app = MockApp()
            mock_app.client.users_info = MagicMock(
                return_value={"user": {"profile": {"display_name": "Test User"}}}
            )
            mock_app.client.chat_postMessage = MagicMock()

            slack_adapter = SlackAdapter(mock_app)

            mock_request = MagicMock(spec=Request)
            mock_request.form = AsyncMock(return_value={
                "channel_id": "C12345678",
                "user_id": "U12345678"
            })

            with pytest.raises(HTTPException) as excinfo:
                await slack_adapter.ask(mock_request)
            assert excinfo.value.status_code == 400
            assert excinfo.value.detail == "Missing parameter in the request."
