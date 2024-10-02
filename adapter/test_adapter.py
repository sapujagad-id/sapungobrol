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
            
            mock_app.client.chat_postMessage = MagicMock(
                side_effect=[
                    {"ts": "1234567890.123456"},  
                    {"ok": True} 
                ]
            )

            slack_adapter = SlackAdapter(mock_app)

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
            mock_app = MockApp()
            mock_app.client.chat_postMessage = MagicMock()

            slack_adapter = SlackAdapter(mock_app)

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