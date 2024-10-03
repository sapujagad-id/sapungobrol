import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import Request, HTTPException
from .slack import SlackAdapter
from slack_sdk.errors import SlackApiError
from chat.chat import ChatOpenAI


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
            
            mock_chatbot = MagicMock(spec=ChatOpenAI)
            mock_chatbot.generate_response.return_value = "Chatbot Reply: I'm fine, thank you!"

            slack_adapter = SlackAdapter(mock_app, mock_chatbot)

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
                text="<@U12345678> asked: \n\n\"How are you?\" "
            )

            mock_app.client.chat_postMessage.assert_any_call(
                channel="C12345678",
                text="Chatbot Reply: I'm fine, thank you!",
                thread_ts="1234567890.123456"
            )

            assert response.status_code == 200

    @pytest.mark.asyncio 
    async def test_missing_parameter_incomplete_text(self):
        with patch('slack_bolt.App') as MockApp:
            mock_app = MockApp()
            mock_app.client.chat_postMessage = MagicMock()
            
            mock_chatbot = MagicMock(spec=ChatOpenAI)

            slack_adapter = SlackAdapter(mock_app, mock_chatbot)

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
            mock_app = MockApp()
            
            mock_app.client.chat_postMessage = MagicMock(
                side_effect=[
                    {"ts": "1234567890.123456"},
                    SlackApiError("Error posting message", response={})
                ]
            )
            mock_app.client.chat_delete = MagicMock()
            
            mock_chatbot = MagicMock(spec=ChatOpenAI)

            slack_adapter = SlackAdapter(mock_app, mock_chatbot)

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
            mock_app = MockApp()
            
            mock_app.client.chat_postMessage = MagicMock(
                side_effect=[
                    {"ts": "1234567890.123456"},
                    SlackApiError("Error posting message", response={})
                ]
            )
            mock_app.client.chat_delete = MagicMock(
                side_effect=SlackApiError("Error delete message", response={})
            )
            
            mock_chatbot = MagicMock(spec=ChatOpenAI)

            slack_adapter = SlackAdapter(mock_app, mock_chatbot)

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
    async def test_success_integration_ask_chat(self):
        with patch('slack_bolt.App') as MockApp, \
             patch('chat.chat.ChatOpenAI') as MockChatOpenAI:
            mock_app = MockApp()
            mock_app.client.users_info = MagicMock(
                return_value={"user": {"profile": {"display_name": "Test User"}}}
            )
            mock_app.client.chat_postMessage = MagicMock(return_value={"ts": "1234567890.123456"})

            mock_chatbot = MockChatOpenAI()
            mock_chatbot.generate_response.return_value = "Chatbot Response: Hello!"

            slack_adapter = SlackAdapter(mock_app, mock_chatbot)

            mock_request = MagicMock(spec=Request)
            mock_request.form = AsyncMock(return_value={
                "channel_id": "C12345678",
                "user_id": "U12345678",
                "text": "12 How is the weather?"
            })

            await slack_adapter.ask(mock_request)

            mock_chatbot.generate_response.assert_called_once_with(query="<@U12345678> asked: \n\n\"How is the weather?\" ")
            
            assert mock_app.client.chat_postMessage.call_count == 2
            mock_app.client.chat_postMessage.assert_any_call(
                channel="C12345678",
                text="<@U12345678> asked: \n\n\"How is the weather?\" "
            )
            mock_app.client.chat_postMessage.assert_any_call(
                channel="C12345678",
                text="Chatbot Response: Hello!",
                thread_ts="1234567890.123456"
            )
    
    @pytest.mark.asyncio
    @patch('chat.chat.ChatOpenAI.generate_response')
    async def test_failing_integration_ask_chat_empty_query(self, mock_generate_response):
        mock_generate_response.return_value = ""
        
        with patch('slack_bolt.App') as MockApp:
            mock_app = MockApp()
            mock_app.client.users_info = MagicMock(
                return_value={"user": {"profile": {"display_name": "Test User"}}}
            )
            mock_app.client.chat_postMessage = MagicMock()

            mock_chatbot = MagicMock(spec=ChatOpenAI)

            slack_adapter = SlackAdapter(mock_app, mock_chatbot)

            mock_request = MagicMock(spec=Request)
            mock_request.form = AsyncMock(return_value={
                "channel_id": "C12345678",
                "user_id": "U12345678",
                "text": ""
            })

            with pytest.raises(HTTPException) as excinfo:
                await slack_adapter.ask(mock_request)
            
            assert excinfo.value.status_code == 400
            assert excinfo.value.detail == "Missing parameter in the request."
            mock_generate_response.assert_not_called()
            mock_app.client.chat_postMessage.assert_not_called()

    @pytest.mark.asyncio
    async def test_edge_case_no_context_in_chat(self):
        with patch('slack_bolt.App') as MockApp, \
             patch('chat.chat.ChatOpenAI') as MockChatOpenAI:
            mock_app = MockApp()
            mock_app.client.users_info = MagicMock(
                return_value={"user": {"profile": {"display_name": "Test User"}}}
            )
            mock_app.client.chat_postMessage = MagicMock(return_value={"ts": "1234567890.123456"})

            mock_chatbot = MockChatOpenAI()
            mock_chatbot.generate_response.return_value = "I'm not sure how to answer that."

            slack_adapter = SlackAdapter(mock_app, mock_chatbot)

            mock_request = MagicMock(spec=Request)
            mock_request.form = AsyncMock(return_value={
                "channel_id": "C12345678",
                "user_id": "U12345678",
                "text": "12 Explain quantum computing"
            })

            await slack_adapter.ask(mock_request)

            mock_chatbot.generate_response.assert_called_once_with(query="<@U12345678> asked: \n\n\"Explain quantum computing\" ")
            assert mock_app.client.chat_postMessage.call_count == 2
            mock_app.client.chat_postMessage.assert_any_call(
                channel="C12345678",
                text="<@U12345678> asked: \n\n\"Explain quantum computing\" "
            )
            mock_app.client.chat_postMessage.assert_any_call(
                channel="C12345678",
                text="I'm not sure how to answer that.",
                thread_ts="1234567890.123456"
            )
