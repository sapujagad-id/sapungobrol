import json
import time
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, call, patch
from uuid import uuid4

import pytest
import requests
from fastapi import HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from slack_sdk.errors import SlackApiError
from slack_sdk.web import WebClient

from auth.repository import AuthRepository, UserModel
from bot.bot import BotResponse, ModelEngine
from bot.helper import relative_time
from bot.repository import BotModel
from bot.service import BotService
from chat import ChatEngineSelector, ChatOpenAI
from chat.exceptions import ChatResponseGenerationError
from common.shared_types import MessageAdapter

from .reaction_event import Reaction
from .reaction_event_repository import ReactionEventRepository
from .slack import EmptyQuestion, MissingChatbot, SlackAdapter
from .slack_dto import SlackConfig
from .slack_repository import WorkspaceDataRepository


class TestSlackAdapter:
    @pytest.fixture
    def mock_slack_adapter(self):
        with patch("slack_bolt.App") as MockApp:
            mock_app = MockApp()
            mock_retriever = MagicMock()
            mock_engine_selector = MagicMock(spec=ChatEngineSelector)
            mock_engine_selector.select_engine.return_value = ChatOpenAI(mock_retriever)
            mock_chatbot = mock_engine_selector.select_engine()
            mock_bot_service = MagicMock(spec=BotService)
            
            mock_reaction_event_repository = MagicMock(spec=ReactionEventRepository)
            mock_session = MagicMock()  # Simulates the session object
            mock_create_session = MagicMock(
                __enter__=MagicMock(return_value=mock_session),  # Mock entering the context
                __exit__=MagicMock(return_value=None),  # Mock exiting the context
            )
            mock_reaction_event_repository.create_session = MagicMock(return_value=mock_create_session)
                
            mock_auth_repository = MagicMock(spec=AuthRepository)
            mock_workspace_data_repository = MagicMock(spec=WorkspaceDataRepository)
            mock_slack_config = SlackConfig(
                slack_bot_token="xoxb-123456789012-123456789012-abcdefabcdef",
                slack_signing_secret="mock_signing_secret",
                slack_client_id="mock_client_id",
                slack_client_secret="mock_client_secret",
                slack_scopes=["channels:read", "chat:write", "reactions:read"],
            )

            mock_client = MagicMock(spec=WebClient)
            mock_client.chat_postMessage = MagicMock()
            mock_client.chat_update = MagicMock()
            mock_client.chat_delete = MagicMock()
            mock_client.conversations_history = MagicMock()
            mock_client.conversations_replies = MagicMock()
            mock_client.users_info = MagicMock()
            mock_client.auth_test = MagicMock()

            slack_adapter = SlackAdapter(
                mock_app,
                mock_engine_selector,
                mock_bot_service,
                mock_reaction_event_repository,
                mock_workspace_data_repository,
                mock_auth_repository,
                mock_slack_config,
            )

            slack_adapter.create_webclient_based_on_team_id = MagicMock(return_value=mock_client)

            return {
                "mock_app": mock_app,
                "mock_chatbot": mock_chatbot,
                "mock_bot_service": mock_bot_service,
                "slack_adapter": slack_adapter,
                "mock_client": mock_client,
                "mock_auth_repository": mock_auth_repository,
                "mock_workspace_data_repository": mock_workspace_data_repository,
            }

    @pytest.fixture
    def only_workspace_slack_adapter(self):
        slack_adapter = SlackAdapter(
            None,
            None,
            None,
            None,
            MagicMock(spec=WorkspaceDataRepository),
            None,
            None,
        )
        return slack_adapter

    @pytest.fixture
    def mock_request(self):
        return MagicMock(spec=Request)

    def mock_user_model(self):
        return UserModel(
            id=str(uuid4()),
            sub="mock_sub_id",
            name="Mock User",
            picture="https://example.com/mock_user_picture.jpg",
            email="user@example.com",
            email_verified=True,
            login_method="google",
            created_at=datetime.now(),
            access_level=1,
        )
  
    @pytest.fixture
    def mock_bot_response_list(self):
        first_bot_slug = "first-bot"
        second_bot_slug = "second-bot"

        mock_bot_response_list = MagicMock(
            return_value=[
                BotResponse(
                    id=uuid4(),
                    name="Bot A",
                    system_prompt="prompt A here",
                    slug=first_bot_slug,
                    model=ModelEngine.OPENAI,
                    adapter=MessageAdapter.SLACK,
                    created_at=datetime.fromisocalendar(2024, 1, 1),
                    updated_at=datetime.fromisocalendar(2024, 1, 1),
                    updated_at_relative=relative_time(datetime.fromisocalendar(2024, 1, 1)),
                ),
                BotResponse(
                    id=uuid4(),
                    name="Bot B",
                    system_prompt="a much longer prompt B here",
                    slug=second_bot_slug,
                    model=ModelEngine.OPENAI,
                    adapter=MessageAdapter.SLACK,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    updated_at_relative=relative_time(datetime.now()),
                ),
            ]
        )

        return first_bot_slug, second_bot_slug, mock_bot_response_list

    @pytest.fixture
    def mock_requests(self):
        return MagicMock(spec=requests)

    @pytest.fixture
    def mock_response(self):
        return MagicMock(spec=requests.Response)

    @pytest.fixture
    def mock_conversations_history(self):
        return {
            "messages": [
                {
                    "user": "U1234567890",
                    "type": "message",
                    "ts": "1731075911.249209",
                    "bot_id": "B1234567890",
                    "app_id": "A1234567890",
                    "text": '<@U9876543210> asked: \n\n"Balls" ',
                    "team": "T1234567890",
                    "thread_ts": "1731075911.249209",
                    "reply_count": 1,
                    "reply_users_count": 1,
                    "latest_reply": "1731075911.854659",
                    "metadata": {
                        "event_type": "chat-data",
                        "event_payload": {"bot_slug": "management-1"},
                    },
                    "reactions": [
                        {"name": "laughing", "users": ["U9876543210"], "count": 1},
                        {"name": "-1", "users": ["U9876543210"], "count": 1},
                    ],
                }
            ]
        }

    @pytest.fixture
    def mock_negative_reaction_event(self):
        return self.mock_reaction_added_event("-1")
    
    @pytest.fixture
    def mock_positive_reaction_event(self):
        return self.mock_reaction_added_event("+1")

    def mock_interaction_form(self):
        return {
            "payload": json.dumps(
                {
                    "channel": {"id": "C12345678"},
                    "user": {"id": "U12345678"},
                    "team": {"id": "T123456"},
                    "state": {
                        "values": {
                            "bots": {
                                "select_chatbot": {"selected_option": {"value": "12"}}
                            },
                            "question": {
                                "question": {"value": "What is the weather today?"}
                            },
                        }
                    },
                    "actions": [{"action_id": "ask_question"}],
                    "response_url": "https://hooks.slack.com/XXXXXXX",
                }
            )
        }

    async def common_mock_request(self, mock_request, text):
        mock_request.form = AsyncMock(
            return_value={
                "channel_id": "C12345678",
                "user_id": "U12345678",
                "text": text,
                "metadata": {
                    "event_type": "chat-data",
                    "event_payload": {"bot_slug": "12"},
                },
            }
        )
        return mock_request

    def common_chat_history(self):
        return {
            "messages": [
                {
                    "text": '<@U07MKR1082Y> asked: \n\n"What is the weather today?"',
                    "user": "U07QCQ3LXDW",
                    "ts": "1234567890.123456",
                },
                {
                    "text": "It's sunny!",
                    "user": "U07QCQ3LXDW",
                    "bot_id": "B07PM4SPSPP",
                    "ts": "1234567890.123457",
                },
                {"text": "Thanks!", "user": "U07QCQ3LXDW", "ts": "1234567890.123458"},
            ]
        }

    async def mock_load_options_request(self, mock_request, action_id: str):
        mock_request.form = AsyncMock(
            return_value={
                "channel_id": "C12345678",
                "user_id": "U12345678",
                "payload": json.dumps(
                    {
                        "type": "block_suggestion",
                        "action_id": action_id,
                        "block_id": "bots",
                        "value": "",
                    }
                ),
            }
        )
        return mock_request

    def mock_reaction_added_event(self, reaction: str):
        return {
            "type": "reaction_added",
            "user": "U1234567890",
            "reaction": reaction,
            "item": {
                "type": "message",
                "channel": "C1234567890",
                "ts": "1731075911.249209",
            },
            "item_user": "U9876543210",
            "event_ts": "1731076540.000900",
        }

    def setup_user_in_auth_repository(self, slack_adapter):
        slack_adapter.auth_respository.find_user_by_email.return_value = self.mock_user_model()

    async def setup_ask_method_test(self, components, mock_request, text, success=True):
        mock_chatbot = components["mock_chatbot"]
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]

        self.setup_user_in_auth_repository(slack_adapter)

        if success:
            mock_client.chat_postMessage.return_value = {"ts": "1234567890.123456"}
        else:
            mock_client.chat_postMessage.side_effect = SlackApiError(
                "Error posting message", response={}
            )

        mock_chatbot.generate_response = MagicMock(return_value = "Chatbot Reply: I'm fine, thank you!")

        slack_adapter.process_chatbot_request = AsyncMock(return_value=Response(status_code=200))

        mock_request = await self.common_mock_request(mock_request, text)

        return slack_adapter, mock_client, mock_chatbot, mock_request

    # Test Methods
    @pytest.mark.asyncio
    async def test_handle_interactions_ask_question(
        self, mock_slack_adapter, mock_request, mock_requests, mock_response
    ):
        components = mock_slack_adapter
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]

        mock_request.form = AsyncMock(return_value=self.mock_interaction_form())

        slack_adapter.ask_v2 = AsyncMock()

        mock_response.status_code = 200
        mock_requests.post.return_value = mock_response

        res = await slack_adapter.handle_interactions(mock_request)

        assert res.status_code == 200

        slack_adapter.ask_v2.assert_called_once_with(
            channel_id="C12345678",
            user_id="U12345678",
            slug="12",
            question="What is the weather today?",
            client=mock_client,
        )

    @pytest.mark.asyncio
    async def test_handle_interactions_ask_question_error(
        self, mock_slack_adapter, mock_request
    ):
        components = mock_slack_adapter
        slack_adapter = components["slack_adapter"]

        mock_request.form = AsyncMock(return_value=self.mock_interaction_form())

        slack_adapter.ask_v2 = AsyncMock(side_effect=EmptyQuestion)
        with pytest.raises(HTTPException) as e:
            await slack_adapter.handle_interactions(mock_request)

        assert e.value.status_code == 400
        assert e.value.detail == EmptyQuestion.message

        slack_adapter.ask_v2 = AsyncMock(side_effect=MissingChatbot)
        with pytest.raises(HTTPException) as e:
            await slack_adapter.handle_interactions(mock_request)

        assert e.value.status_code == 400
        assert e.value.detail == MissingChatbot.message

    @pytest.mark.asyncio
    async def test_handle_interactions_ask_question_slack_api_error(
        self, mock_slack_adapter, mock_request, mock_response
    ):
        components = mock_slack_adapter
        slack_adapter = components["slack_adapter"]

        mock_request.form = AsyncMock(return_value=self.mock_interaction_form())

        slack_adapter.ask_v2 = AsyncMock()

        with patch("requests.post") as mock_post:
            mock_response.status_code = 400
            mock_post.return_value = mock_response
            await slack_adapter.handle_interactions(mock_request)

            mock_post.side_effect = requests.RequestException
            await slack_adapter.handle_interactions(mock_request)

    @pytest.mark.asyncio
    async def test_load_options_select_chatbot(
        self, mock_slack_adapter, mock_bot_response_list, mock_request
    ):
        components = mock_slack_adapter
        mock_bot_service = components["mock_bot_service"]
        slack_adapter = components["slack_adapter"]

        _, _, mock_bot_list = mock_bot_response_list

        mock_request = await self.mock_load_options_request(mock_request, action_id="select_chatbot")
        mock_bot_service.get_chatbots = mock_bot_list

        res = await slack_adapter.load_options(mock_request)
        options = res["options"]
        bots = mock_bot_list.return_value

        assert len(bots) == len(options)

        for i in range(len(options)):
            assert options[i]["value"] == bots[i].slug

    @pytest.mark.asyncio
    async def test_load_options_unknown_action(self, mock_slack_adapter, mock_request):
        components = mock_slack_adapter
        slack_adapter = components["slack_adapter"]

        mock_request = await self.mock_load_options_request(mock_request, action_id="unknown")

        res = await slack_adapter.load_options(mock_request)

        assert res.status_code == 200

    @pytest.mark.asyncio
    async def test_reaction_added(self, mock_negative_reaction_event, mock_slack_adapter):
        negative_reaction = mock_negative_reaction_event
        components = mock_slack_adapter
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]

        context = {"team_id": "T1234567"}

        slack_adapter.handle_rating_reaction = MagicMock()
        res = slack_adapter.reaction_added(negative_reaction, context)

        assert res.status_code == 200

        slack_adapter.handle_rating_reaction.assert_called_once_with(negative_reaction, mock_client)

    @pytest.mark.asyncio
    async def test_negative_reaction(
        self, mock_negative_reaction_event, mock_slack_adapter, mock_conversations_history
    ):
        negative_reaction = mock_negative_reaction_event
        components = mock_slack_adapter
        mock_bot_service = components["mock_bot_service"]
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]

        mock_client.conversations_history.return_value = mock_conversations_history

        mock_bot_service.get_chatbot_by_slug.return_value = BotResponse(
            id=uuid4(),
            name="Bot B",
            system_prompt="a much longer prompt B here",
            slug="management-1",
            model=ModelEngine.OPENAI,
            adapter=MessageAdapter.SLACK,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            updated_at_relative=relative_time(datetime.now()),
        )

        slack_adapter.handle_rating_reaction(event=negative_reaction, client=mock_client)

        mock_client.conversations_history.assert_called_once()
        mock_bot_service.get_chatbot_by_slug.assert_called_once()
        slack_adapter.reaction_event_repository.create_reaction_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_negative_reaction_not_parent_message(
        self, mock_negative_reaction_event, mock_slack_adapter, mock_conversations_history
    ):
        negative_reaction = mock_negative_reaction_event
        components = mock_slack_adapter
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]

        conversations_history = mock_conversations_history
        conversations_history["messages"][0]["thread_ts"] = "completely-different-id"

        mock_client.conversations_history.return_value = conversations_history

        slack_adapter.handle_rating_reaction(event=negative_reaction, client=mock_client)

        mock_client.conversations_history.assert_called_once()
        slack_adapter.reaction_event_repository.create_reaction_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_negative_reaction_no_metadata(
        self, mock_negative_reaction_event, mock_slack_adapter, mock_conversations_history
    ):
        negative_reaction = mock_negative_reaction_event
        components = mock_slack_adapter
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]

        conversations_history = mock_conversations_history
        conversations_history["messages"][0]["metadata"] = None

        mock_client.conversations_history.return_value = conversations_history

        slack_adapter.handle_rating_reaction(event=negative_reaction, client=mock_client)

        mock_client.conversations_history.assert_called_once()
        slack_adapter.reaction_event_repository.create_reaction_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_negative_reaction_invalid_event(
        self, mock_negative_reaction_event, mock_slack_adapter, mock_conversations_history
    ):
        negative_reaction = mock_negative_reaction_event
        components = mock_slack_adapter
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]

        conversations_history = mock_conversations_history
        conversations_history["messages"][0]["metadata"]["event_type"] = "some-random-event"

        mock_client.conversations_history.return_value = conversations_history

        slack_adapter.handle_rating_reaction(event=negative_reaction, client=mock_client)

        mock_client.conversations_history.assert_called_once()
        slack_adapter.reaction_event_repository.create_reaction_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_negative_reaction_chatbot_not_found(
        self, mock_negative_reaction_event, mock_slack_adapter, mock_conversations_history
    ):
        negative_reaction = mock_negative_reaction_event
        components = mock_slack_adapter
        mock_bot_service = components["mock_bot_service"]
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]

        mock_client.conversations_history.return_value = mock_conversations_history

        mock_bot_service.get_chatbot_by_slug.return_value = None

        slack_adapter.handle_rating_reaction(event=negative_reaction, client=mock_client)

        mock_client.conversations_history.assert_called_once()
        slack_adapter.reaction_event_repository.create_reaction_event.assert_not_called()


    def test_remove_reaction(self, mock_slack_adapter):
        components = mock_slack_adapter
        slack_adapter = components["slack_adapter"]
        reaction_event_repository = slack_adapter.reaction_event_repository

        event = {
            "item": {
                "ts": "1234567890.123456"
            },
            "user": "U12345678",
            "reaction": "-1"
        }

        reaction = event["reaction"]

        with patch.object(slack_adapter, 'logger', return_value=MagicMock()) as mock_logger:
            slack_adapter.remove_reaction(event, reaction)
            mock_logger.return_value.info.assert_called_once_with("handle negative reaction removed")

        reaction_event_repository.delete_reaction_event.assert_called_once_with(
            reaction,
            ("1234567890.123456",),
            ("U12345678",)
        )

    def test_reaction_removed_negative_reaction(self, mock_slack_adapter):
        components = mock_slack_adapter
        slack_adapter = components["slack_adapter"]

        slack_adapter.remove_reaction = MagicMock()

        event = {
            "reaction": "-1",
            "item": {
                "ts": "1234567890.123456"
            },
            "user": "U12345678"
        }

        response = slack_adapter.reaction_removed(event)

        slack_adapter.remove_reaction.assert_called_once_with(event, Reaction.NEGATIVE)

        assert response.status_code == 200


    @pytest.mark.asyncio
    async def test_positive_reaction(
        self, mock_positive_reaction_event, mock_slack_adapter, mock_conversations_history
    ):
        positive_reaction = mock_positive_reaction_event
        components = mock_slack_adapter
        mock_bot_service = components["mock_bot_service"]
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]

        mock_client.conversations_history.return_value = mock_conversations_history

        mock_bot_service.get_chatbot_by_slug.return_value = BotResponse(
            id=uuid4(),
            name="Bot A",
            system_prompt="a prompt for Bot A",
            slug="management-2",
            model=ModelEngine.OPENAI,
            adapter=MessageAdapter.SLACK,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            updated_at_relative=relative_time(datetime.now()),
        )

        slack_adapter.handle_rating_reaction(event=positive_reaction, client=mock_client)

        mock_client.conversations_history.assert_called_once()
        mock_bot_service.get_chatbot_by_slug.assert_called_once()
        slack_adapter.reaction_event_repository.create_reaction_event.assert_called_once()


    @pytest.mark.asyncio
    async def test_positive_reaction_not_parent_message(
        self, mock_positive_reaction_event, mock_slack_adapter, mock_conversations_history
    ):
        positive_reaction = mock_positive_reaction_event
        components = mock_slack_adapter
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]

        conversations_history = mock_conversations_history
        conversations_history["messages"][0]["thread_ts"] = "different-thread-id"

        mock_client.conversations_history.return_value = conversations_history

        slack_adapter.handle_rating_reaction(event=positive_reaction, client=mock_client)

        mock_client.conversations_history.assert_called_once()
        slack_adapter.reaction_event_repository.create_reaction_event.assert_not_called()


    @pytest.mark.asyncio
    async def test_positive_reaction_no_metadata(
        self, mock_positive_reaction_event, mock_slack_adapter, mock_conversations_history
    ):
        positive_reaction = mock_positive_reaction_event
        components = mock_slack_adapter
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]

        conversations_history = mock_conversations_history
        conversations_history["messages"][0]["metadata"] = None

        mock_client.conversations_history.return_value = conversations_history

        slack_adapter.handle_rating_reaction(event=positive_reaction, client=mock_client)

        mock_client.conversations_history.assert_called_once()
        slack_adapter.reaction_event_repository.create_reaction_event.assert_not_called()


    @pytest.mark.asyncio
    async def test_positive_reaction_invalid_event(
        self, mock_positive_reaction_event, mock_slack_adapter, mock_conversations_history
    ):
        positive_reaction = mock_positive_reaction_event
        components = mock_slack_adapter
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]

        conversations_history = mock_conversations_history
        conversations_history["messages"][0]["metadata"]["event_type"] = "unknown-event-type"

        mock_client.conversations_history.return_value = conversations_history

        slack_adapter.handle_rating_reaction(event=positive_reaction, client=mock_client)

        mock_client.conversations_history.assert_called_once()
        slack_adapter.reaction_event_repository.create_reaction_event.assert_not_called()


    @pytest.mark.asyncio
    async def test_positive_reaction_chatbot_not_found(
        self, mock_positive_reaction_event, mock_slack_adapter, mock_conversations_history
    ):
        positive_reaction = mock_positive_reaction_event
        components = mock_slack_adapter
        mock_bot_service = components["mock_bot_service"]
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]

        mock_client.conversations_history.return_value = mock_conversations_history

        mock_bot_service.get_chatbot_by_slug.return_value = None

        slack_adapter.handle_rating_reaction(event=positive_reaction, client=mock_client)

        mock_client.conversations_history.assert_called_once()
        slack_adapter.reaction_event_repository.create_reaction_event.assert_not_called()


    @pytest.mark.asyncio
    async def test_ask_form(self, mock_slack_adapter, mock_request):
        components = mock_slack_adapter
        slack_adapter = components["slack_adapter"]

        mock_request = await self.common_mock_request(mock_request, "12 What")

        res = slack_adapter.ask_form(mock_request)

        assert res["blocks"] is not None

    @pytest.mark.asyncio
    async def test_send_generated_response(self, mock_slack_adapter):
        components = mock_slack_adapter
        mock_chatbot = components["mock_chatbot"]
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]

        mock_client.chat_postMessage = MagicMock()
        mock_client.chat_update = MagicMock()

        mock_client.chat_postMessage.side_effect = [
            {"ts": "1234567890.123456"},
            {"ts": "1234567890.654321"},
        ]
        mock_chatbot.generate_response = MagicMock(return_value = "I'm fine, thank you!")

        slack_adapter.send_generated_response(
            "C12345678", "1234567890.654321", mock_chatbot, "How are you?", 1, mock_client
        )
        mock_client.chat_update.assert_called_once_with(
            channel="C12345678", ts="1234567890.654321", text="I'm fine, thank you!"
        )

    @pytest.mark.asyncio
    async def test_send_generated_response_generation_error(self, mock_slack_adapter):
        components = mock_slack_adapter
        mock_chatbot = components["mock_chatbot"]
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]

        mock_client.chat_postMessage = MagicMock()
        mock_client.chat_update = MagicMock()

        mock_client.chat_postMessage.side_effect = [
            {"ts": "1234567890.123456"},
            {"ts": "1234567890.654321"},
        ]
        mock_chatbot.generate_response = MagicMock(side_effect = ChatResponseGenerationError)

        slack_adapter.send_generated_response(
            "C12345678", "1234567890.654321", mock_chatbot, "How are you?", 1, mock_client
        )

        mock_client.chat_update.assert_called_once_with(
            channel="C12345678",
            ts="1234567890.654321",
            text="Something went wrong when trying to generate your response.",
        )

    @pytest.mark.asyncio
    async def test_ask_v2(self, mock_slack_adapter):
        components = mock_slack_adapter
        mock_chatbot = components["mock_chatbot"]
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]

        mock_client.chat_postMessage = MagicMock()

        mock_client.chat_postMessage.return_value = {"ts": "1234567890.123456"}

        mock_chatbot.generate_response = MagicMock(return_value = "Chatbot Reply: I'm fine, thank you!")

        slack_adapter.process_chatbot_request = AsyncMock(return_value=Response(status_code=200))

        response = await slack_adapter.ask_v2(
            channel_id="C12345678",
            user_id="U12345678",
            slug="12",
            question="How are you?",
            client=mock_client,
        )

        mock_client.chat_postMessage.assert_called_once_with(
            channel="C12345678",
            text='<@U12345678> asked: \n\n"How are you?" ',
            metadata={"event_type": "chat-data", "event_payload": {"bot_slug": "12"}},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_ask_v2_slack_api_error(self, mock_slack_adapter):
        components = mock_slack_adapter
        mock_chatbot = components["mock_chatbot"]
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]

        mock_client.chat_postMessage.side_effect = SlackApiError(
            "Error posting message", response={}
        )

        mock_chatbot.generate_response = MagicMock(return_value = "Chatbot Reply: I'm fine, thank you!")

        slack_adapter.process_chatbot_request = AsyncMock(return_value=Response(status_code=200))

        with pytest.raises(HTTPException) as exc_info:
            await slack_adapter.ask_v2(
                channel_id="C12345678",
                user_id="U12345678",
                slug="12",
                question="How are you?",
                client=mock_client,
            )

        assert exc_info.value.status_code == 400
        assert "Slack API Error" in str(exc_info.value.detail)

        mock_client.chat_postMessage.assert_called_once_with(
            channel="C12345678",
            text='<@U12345678> asked: \n\n"How are you?" ',
            metadata={"event_type": "chat-data", "event_payload": {"bot_slug": "12"}},
        )

    @pytest.mark.asyncio
    async def test_ask_v2_no_bots(self, mock_slack_adapter):
        components = mock_slack_adapter
        mock_bot_service = components["mock_bot_service"]
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]

        mock_client.chat_postMessage.return_value = {"ts": "1234567890.123456"}

        mock_bot_service.get_chatbot_by_slug.return_value = None

        with pytest.raises(MissingChatbot):
            await slack_adapter.ask_v2(
                channel_id="C12345678",
                user_id="U12345678",
                slug="12",
                question="How are you?",
                client=mock_client,
            )

    @pytest.mark.asyncio
    async def test_ask_v2_empty_question(self, mock_slack_adapter):
        components = mock_slack_adapter
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]

        mock_client.chat_postMessage.return_value = {"ts": "1234567890.123456"}

        with pytest.raises(EmptyQuestion):
            await slack_adapter.ask_v2(
                channel_id="C12345678",
                user_id="U12345678",
                slug="12",
                question=None,
                client=mock_client,
            )

        with pytest.raises(EmptyQuestion):
            await slack_adapter.ask_v2(
                channel_id="C12345678",
                user_id="U12345678",
                slug="12",
                question="",
                client=mock_client,
            )

    @pytest.mark.asyncio
    async def test_ask_v2_user_not_found(self, mock_slack_adapter):
        components = mock_slack_adapter
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]
        mock_auth_repository = components["mock_auth_repository"]

        mock_client.users_info.return_value = {
            "user": {"profile": {"email": "nonexistent_user@example.com"}}
        }
        mock_auth_repository.find_user_by_email.return_value = None
        mock_client.chat_postMessage.return_value = {"ts": "1234567890.123456"}

        await slack_adapter.ask_v2(
            channel_id="C12345678",
            user_id="U12345678",
            slug="test-bot-slug",
            question="What's the answer to life?",
            client=mock_client,
        )

        mock_auth_repository.find_user_by_email.assert_called_with(
            "nonexistent_user@example.com"
        )

        expected_calls = [
            call(
                channel="C12345678",
                text='<@U12345678> asked: \n\n"What\'s the answer to life?" ',
                metadata={
                    "event_type": "chat-data",
                    "event_payload": {"bot_slug": "test-bot-slug"},
                },
            ),
            call(
                channel="C12345678",
                text=":hourglass_flowing_sand: Processing your request, please wait...",
                thread_ts="1234567890.123456",
            ),
        ]
        mock_client.chat_postMessage.assert_has_calls(expected_calls, any_order=False)

    @pytest.mark.asyncio
    async def test_ask_method(self, mock_slack_adapter, mock_request):
        components = mock_slack_adapter
        slack_adapter, mock_client, _, mock_request = await self.setup_ask_method_test(
            components, mock_request, "12 How are you?", success=True
        )

        response = await slack_adapter.ask(mock_request)

        mock_client.chat_postMessage.assert_called_once_with(
            channel="C12345678",
            text='<@U12345678> asked: \n\n"How are you?" ',
            metadata={"event_type": "chat-data", "event_payload": {"bot_slug": "12"}},
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_ask_method_slack_api_error(self, mock_slack_adapter, mock_request):
        components = mock_slack_adapter
        slack_adapter, mock_client, _, mock_request = await self.setup_ask_method_test(
            components, mock_request, "12 How are you?", success=False
        )

        with pytest.raises(HTTPException) as exc_info:
            await slack_adapter.ask(mock_request)

        assert exc_info.value.status_code == 400
        assert "Slack API Error" in str(exc_info.value.detail)

        mock_client.chat_postMessage.assert_called_once_with(
            channel="C12345678",
            text='<@U12345678> asked: \n\n"How are you?" ',
            metadata={"event_type": "chat-data", "event_payload": {"bot_slug": "12"}},
        )

    @pytest.mark.asyncio
    async def test_missing_parameter_incomplete_text(self, mock_slack_adapter, mock_request):
        components = mock_slack_adapter
        slack_adapter = components["slack_adapter"]

        mock_request = await self.common_mock_request(mock_request, "12")

        res = await slack_adapter.ask(mock_request)
        assert res["text"] == "Missing parameter in the request."


    async def perform_ask_chat_test(
        self, mock_slack_adapter, mock_request, find_user_by_email_return_value, query_text
    ):
        components = mock_slack_adapter
        mock_chatbot = components["mock_chatbot"]
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]

        slack_adapter.auth_respository.find_user_by_email.return_value = find_user_by_email_return_value

        mock_client.users_info.return_value = {
            "user": {
                "profile": {"display_name": "Test User", "email": "user@broom.id"}
            }
        }
        mock_client.chat_postMessage.return_value = {"ts": "1234567890.123456"}
        mock_chatbot.generate_response = MagicMock(return_value = "Chatbot Response: Hello!")

        mock_request = await self.common_mock_request(mock_request, query_text)

        await slack_adapter.ask(mock_request)
        time.sleep(1)

        return components, mock_request, mock_chatbot, mock_client

    @pytest.mark.asyncio
    async def test_success_integration_ask_chat(self, mock_slack_adapter, mock_request):
        user_model = self.mock_user_model()
        _, mock_request, mock_chatbot, mock_client = await self.perform_ask_chat_test(
            mock_slack_adapter, mock_request, user_model, "12 How is the weather?"
        )

        mock_chatbot.generate_response.assert_called_once_with(
            query='<@U12345678> asked: \n\n"How is the weather?" ', access_level=1
        )

        assert mock_client.chat_postMessage.call_count == 2
        mock_client.chat_postMessage.assert_any_call(
            channel="C12345678",
            text='<@U12345678> asked: \n\n"How is the weather?" ',
            metadata={"event_type": "chat-data", "event_payload": {"bot_slug": "12"}},
        )
        mock_client.chat_update.assert_called_once_with(
            channel="C12345678", ts="1234567890.123456", text="Chatbot Response: Hello!"
        )


    @pytest.mark.asyncio
    async def test_success_integration_ask_chat_no_access_level(
        self, mock_slack_adapter, mock_request
    ):
        _, mock_request, mock_chatbot, mock_client = await self.perform_ask_chat_test(
            mock_slack_adapter, mock_request, None, "12 How is the weather?"
        )

        # Assertions
        mock_chatbot.generate_response.assert_called_once_with(
            query='<@U12345678> asked: \n\n"How is the weather?" ', access_level=1
        )
        assert mock_client.chat_postMessage.call_count == 2
        mock_client.chat_postMessage.assert_any_call(
            channel="C12345678",
            text='<@U12345678> asked: \n\n"How is the weather?" ',
            metadata={"event_type": "chat-data", "event_payload": {"bot_slug": "12"}},
        )
        mock_client.chat_update.assert_called_once_with(
            channel="C12345678", ts="1234567890.123456", text="Chatbot Response: Hello!"
        )

    @pytest.mark.asyncio
    async def test_failing_integration_ask_chat_empty_query(
        self, mock_slack_adapter, mock_request
    ):
        components = mock_slack_adapter
        mock_chatbot = components["mock_chatbot"]
        slack_adapter = components["slack_adapter"]

        mock_chatbot.generate_response = MagicMock(return_value = "")

        mock_request = await self.common_mock_request(mock_request, "")

        res = await slack_adapter.ask(mock_request)
        assert res["text"] == "Missing parameter in the request."

    @pytest.mark.asyncio
    async def test_edge_case_no_context_in_chat(self, mock_slack_adapter, mock_request):
        components = mock_slack_adapter
        mock_chatbot = components["mock_chatbot"]
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]
        self.setup_user_in_auth_repository(slack_adapter)

        mock_client.users_info.return_value = {
            "user": {
                "profile": {"display_name": "Test User", "email": "user@broom.id"}
            }
        }
        mock_client.chat_postMessage.return_value = {"ts": "1234567890.123456"}

        mock_chatbot.generate_response = MagicMock(return_value = "I'm not sure how to answer that.")

        mock_request = await self.common_mock_request(mock_request, "12 Explain quantum computing")

        await slack_adapter.ask(mock_request)

        time.sleep(1)

        mock_chatbot.generate_response.assert_called_once_with(
            query='<@U12345678> asked: \n\n"Explain quantum computing" ', access_level=1
        )
        assert mock_client.chat_postMessage.call_count == 2
        mock_client.chat_postMessage.assert_any_call(
            channel="C12345678",
            text='<@U12345678> asked: \n\n"Explain quantum computing" ',
            metadata={"event_type": "chat-data", "event_payload": {"bot_slug": "12"}},
        )
        mock_client.chat_update.assert_called_once_with(
            channel="C12345678", ts="1234567890.123456", text="I'm not sure how to answer that."
        )

    @pytest.mark.asyncio
    async def test_ask_no_bots(self, mock_slack_adapter, mock_request):
        components = mock_slack_adapter
        mock_bot_service = components["mock_bot_service"]
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]

        mock_client.chat_postMessage.return_value = {"ts": "1234567890.123456"}

        mock_bot_service.get_chatbot_by_slug.return_value = None

        req = await self.common_mock_request(mock_request, "12 Explain quantum computing")

        with pytest.raises(MissingChatbot):
            await slack_adapter.ask(req)

    @pytest.mark.asyncio
    async def test_list_bots_method(
        self, mock_slack_adapter, mock_request, mock_bot_response_list
    ):
        components = mock_slack_adapter
        mock_bot_service = components["mock_bot_service"]
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]

        mock_client.chat_postMessage.return_value = {"ts": "1234567890.123456"}

        first_bot_slug, second_bot_slug, mock_bot_service.get_chatbots = mock_bot_response_list

        mock_request = await self.common_mock_request(mock_request, "")

        response = await slack_adapter.list_bots(mock_request)

        assert mock_client.chat_postMessage.call_count == 1

        mock_client.chat_postMessage.assert_any_call(
            channel="C12345678",
            text=f"2 Active Bot(s)\n- Bot A ({first_bot_slug})\n- Bot B ({second_bot_slug})",
        )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_bots_method_post_message_failure(
        self, mock_slack_adapter, mock_request, mock_bot_response_list
    ):
        components = mock_slack_adapter
        mock_bot_service = components["mock_bot_service"]
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]

        mock_client.chat_postMessage.side_effect = SlackApiError(
            "Error posting message", response={}
        )

        _, _, mock_bot_service.get_chatbots = mock_bot_response_list

        mock_request = await self.common_mock_request(mock_request, "")

        with pytest.raises(HTTPException) as excinfo:
            await slack_adapter.list_bots(mock_request)
        assert excinfo.value.status_code == 400
        assert "Slack API Error" in excinfo.value.detail
        assert mock_client.chat_postMessage.call_count == 1

    def test_event_message_without_thread(self, mock_slack_adapter):
        components = mock_slack_adapter
        slack_adapter = components["slack_adapter"]
        slack_adapter.event_message_replied = MagicMock()

        event = {
            "type": "message",
            "channel": "C123ABC456",
            "user": "U123ABC456",
            "text": "Hello world",
            "ts": "1355517523.000005",
        }

        slack_adapter.event_message(event)

        slack_adapter.event_message_replied.assert_not_called()

    def test_event_message_with_thread_wrong_user(self, mock_slack_adapter):
        components = mock_slack_adapter
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]

        event = {
            "thread_ts": "1355517523.000005",
            "channel": "C123ABC456",
            "team": "T0123456",
        }

        slack_adapter.app.client.conversations_history.return_value = {
            "messages": [
                {
                    "user": "U123NONBOT",
                    "text": '<@U07N64EUJ8Y> asked:\n\n"hello"',
                    "metadata": "test metadata",
                }
            ]
        }

        mock_client.auth_test.return_value = {"user_id": "UV123456"}

        slack_adapter.bot_replied = MagicMock()

        slack_adapter.event_message(event)

        slack_adapter.bot_replied.assert_not_called()

    def test_event_message_with_thread_wrong_parent_message(self, mock_slack_adapter):
        components = mock_slack_adapter
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]

        event = {
            "thread_ts": "1355517523.000005",
            "channel": "C123ABC456",
            "team": "T0123456",
        }

        slack_adapter.app.client.conversations_history.return_value = {
            "messages": [{"user": "U2111", "text": "This is a random message"}]
        }

        mock_client.auth_test.return_value = {"user_id": "UV123456"}

        slack_adapter.bot_replied = MagicMock()

        slack_adapter.event_message(event)

        slack_adapter.bot_replied.assert_not_called()

    def test_event_message_with_thread_bot_replied(self, mock_slack_adapter):
        components = mock_slack_adapter
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]

        event = {
            "thread_ts": "1355517523.000005",
            "channel": "C123ABC456",
            "text": "How are you?",
            "user": "UV123456",
            "team": "T0123456",
        }

        parent_messages = {
            "messages": [
                {
                    "text": '<@U07N64EUJ8Y> asked:\n\n"hello"',
                    "metadata": {"event_payload": {"bot_slug": "test-bot"}},
                    "user": "UV123456",
                }
            ]
        }

        mock_client.conversations_history.return_value = parent_messages
        mock_client.auth_test.return_value = {"user_id": "UV123456"}

        slack_adapter.bot_replied = MagicMock()

        slack_adapter.event_message_replied(event)

        mock_client.conversations_history.assert_called_once_with(
            channel="C123ABC456",
            inclusive=True,
            oldest="1355517523.000005",
            limit=1,
            include_all_metadata=True,
        )

        slack_adapter.bot_replied.assert_called_once_with(
            event, parent_messages, mock_client
        )

    def setup_bot_replied_test(
        self,
        mock_slack_adapter,
        user_in_auth_repository=True,
    ):
        components = mock_slack_adapter
        slack_adapter = components["slack_adapter"]
        mock_chatbot = components["mock_chatbot"]
        mock_client = components["mock_client"]

        if user_in_auth_repository:
            self.setup_user_in_auth_repository(slack_adapter)
        else:
            slack_adapter.auth_respository.find_user_by_email.return_value = None

        event = {
            "thread_ts": "1355517523.000005",
            "channel": "C123ABC456",
            "text": "How are you?",
            "user": "UV123456",
        }
        parent_messages = {
            "messages": [
                {
                    "text": '<@U07N64EUJ8Y> asked:\n\n"hello"',
                    "metadata": {"event_payload": {"bot_slug": "test-bot"}},
                }
            ]
        }

        mock_client.users_info.return_value = {
            "user": {"profile": {"email": "user@example.com"}}
        }
        slack_adapter.bot_service.get_chatbot_by_slug.return_value = mock_chatbot
        slack_adapter.process_chatbot_request = AsyncMock(return_value={"status_code": 200})
        slack_adapter.get_chat_history = MagicMock(
            return_value=[
                {"role": "user", "content": "How are you ?"},
                {"role": "assistant", "content": "Fine"},
            ]
        )

        return components, event, parent_messages, slack_adapter, mock_chatbot, mock_client

    def test_bot_replied(self, mock_slack_adapter):
        (
            _,
            event,
            parent_messages,
            slack_adapter,
            mock_chatbot,
            mock_client,
        ) = self.setup_bot_replied_test(mock_slack_adapter, user_in_auth_repository=True)

        response = slack_adapter.bot_replied(event, parent_messages, mock_client)

        slack_adapter.bot_service.get_chatbot_by_slug.assert_called_once_with(
            slug="test-bot"
        )
        slack_adapter.process_chatbot_request.assert_called_once_with(
            mock_chatbot,
            "How are you?",
            "C123ABC456",
            "1355517523.000005",
            client=mock_client,
            access_level=1,
            history=[
                {"role": "user", "content": "How are you ?"},
                {"role": "assistant", "content": "Fine"},
            ],
        )
        assert response == {"status_code": 200}

    def test_bot_replied_no_access_level(self, mock_slack_adapter):
        (
            components,
            event,
            parent_messages,
            slack_adapter,
            mock_chatbot,
            mock_client,
        ) = self.setup_bot_replied_test(mock_slack_adapter, user_in_auth_repository=False)

        response = slack_adapter.bot_replied(event, parent_messages, mock_client)

        slack_adapter.bot_service.get_chatbot_by_slug.assert_called_once_with(
            slug="test-bot"
        )
        slack_adapter.process_chatbot_request.assert_called_once_with(
            mock_chatbot,
            "How are you?",
            "C123ABC456",
            "1355517523.000005",
            client=mock_client,
            access_level=1,
            history=[
                {"role": "user", "content": "How are you ?"},
                {"role": "assistant", "content": "Fine"},
            ],
        )
        assert response == {"status_code": 200}

    def test_bot_replied_chatbot_not_found(self, mock_slack_adapter):
        components = mock_slack_adapter
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]
        self.setup_user_in_auth_repository(slack_adapter)

        slack_adapter.bot_service.get_chatbot_by_slug.return_value = None

        event = {
            "thread_ts": "1355517523.000005",
            "channel": "C123ABC456",
            "text": "How are you?",
            "user": "UV123456",
        }
        parent_messages = {
            "messages": [
                {
                    "user": "A2130123",
                    "text": '<@U07N64EUJ8Y> asked:\n\n"hello"',
                    "metadata": {"event_payload": {"bot_slug": "non-existent-bot"}},
                }
            ]
        }

        mock_client.users_info.return_value = {
            "user": {"profile": {"email": "user@example.com"}}
        }

        with pytest.raises(MissingChatbot):
            slack_adapter.bot_replied(event, parent_messages, mock_client)

        slack_adapter.bot_service.get_chatbot_by_slug.assert_called_once_with(
            slug="non-existent-bot"
        )

    def test_get_chat_history(self, mock_slack_adapter):
        components = mock_slack_adapter
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]

        event = {"channel": "C12345678", "thread_ts": "1234567890.123456"}

        mock_conversation_replies = self.common_chat_history()

        mock_client.conversations_replies.return_value = mock_conversation_replies

        result = slack_adapter.get_chat_history(event, mock_client)

        expected_result = [
            {"role": "user", "content": "What is the weather today?"},
            {"role": "assistant", "content": "It's sunny!"},
            {"role": "user", "content": "Thanks!"},
        ]

        assert result == expected_result
        mock_client.conversations_replies.assert_called_once_with(
            channel="C12345678",
            inclusive=True,
            ts="1234567890.123456",
            include_all_metadata=True,
        )

    @pytest.mark.asyncio
    async def test_process_chatbot_request_with_history(self, mock_slack_adapter):
        components = mock_slack_adapter
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]
        mock_chatbot = components["mock_chatbot"]

        channel_id = "C12345678"
        thread_ts = "1234567890.123456"
        history = [
            {"role": "user", "content": "What is the weather today?"},
            {"role": "assistant", "content": "It's sunny!"},
            {"role": "user", "content": "1 + 1 ?"},
            {"role": "assistant", "content": "1 + 1 = 2"},
        ]

        mock_client.chat_postMessage.return_value = {"ts": "1234567890.654321"}

        mock_chatbot.add_chat_history = MagicMock()

        bot = BotModel()
        bot.model = mock_chatbot

        with patch("threading.Thread") as mock_thread:
            response = await slack_adapter.process_chatbot_request(
                chatbot=bot,
                question="Is it sunny outside?",
                channel_id=channel_id,
                thread_ts=thread_ts,
                client=mock_client,
                access_level=1,
                history=history,
            )

            mock_client.chat_postMessage.assert_called_once_with(
                channel=channel_id,
                text=":hourglass_flowing_sand: Processing your request, please wait...",
                thread_ts=thread_ts,
            )

            expected_calls = [
                call(event["role"], event["content"]) for event in history
            ]
            mock_chatbot.add_chat_history.assert_has_calls(
                expected_calls, any_order=False
            )

            mock_thread.assert_called_once()
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_process_chatbot_request_slack_api_error(self, mock_slack_adapter):
        components = mock_slack_adapter
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]
        mock_chatbot = components["mock_chatbot"]

        channel_id = "C12345678"
        thread_ts = "1234567890.123456"
        history = [
            {"role": "user", "content": "What is the weather today?"},
            {"role": "assistant", "content": "It's sunny!"},
            {"role": "user", "content": "1 + 1 ?"},
            {"role": "assistant", "content": "1 + 1 = 2"},
        ]

        mock_client.chat_postMessage.side_effect = SlackApiError(
            "Error posting message", response={}
        )

        bot = BotModel()
        bot.model = mock_chatbot

        with pytest.raises(HTTPException) as excinfo:
            await slack_adapter.process_chatbot_request(
                chatbot=bot,
                question="Is it sunny outside?",
                channel_id=channel_id,
                thread_ts=thread_ts,
                client=mock_client,
                access_level=1,
                history=history,
            )

        assert excinfo.value.status_code == 400
        assert "Slack API Error" in str(excinfo.value.detail)

        mock_client.chat_postMessage.assert_called_once_with(
            channel=channel_id,
            text=":hourglass_flowing_sand: Processing your request, please wait...",
            thread_ts=thread_ts,
        )

    @pytest.mark.asyncio
    async def test_process_chatbot_request_slack_api_error_during_delete(
        self, mock_slack_adapter
    ):
        components = mock_slack_adapter
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]
        mock_chatbot = components["mock_chatbot"]

        channel_id = "C12345678"
        thread_ts = "1234567890.123456"
        history = [
            {"role": "user", "content": "What is the weather today?"},
            {"role": "assistant", "content": "It's sunny!"},
            {"role": "user", "content": "1 + 1 ?"},
            {"role": "assistant", "content": "1 + 1 = 2"},
        ]

        mock_client.chat_postMessage.side_effect = SlackApiError(
            "Error posting message", response={}
        )
        mock_client.chat_delete.side_effect = SlackApiError(
            "Error deleting message", response={}
        )

        bot = BotModel()
        bot.model = mock_chatbot

        with pytest.raises(HTTPException) as excinfo:
            await slack_adapter.process_chatbot_request(
                chatbot=bot,
                question="Is it sunny outside?",
                channel_id=channel_id,
                thread_ts=thread_ts,
                client=mock_client,
                access_level=1,
                history=history,
            )

        assert excinfo.value.status_code == 400
        assert "Slack API Error: Error deleting message" in str(excinfo.value.detail)

        mock_client.chat_postMessage.assert_called_once_with(
            channel=channel_id,
            text=":hourglass_flowing_sand: Processing your request, please wait...",
            thread_ts=thread_ts,
        )
        mock_client.chat_delete.assert_called_once_with(
            channel=channel_id,
            ts=thread_ts,
        )

    def test_fail_extract_question(self, mock_slack_adapter):
        components = mock_slack_adapter
        slack_adapter = components["slack_adapter"]
        mock_client = components["mock_client"]

        event = {"channel": "C12345678", "thread_ts": "1234567890.123456"}

        mock_conversation_replies = {
            "messages": [
                {
                    "text": '<@U07MKR1082Y> sked: \n\n"What is the weather today?"',
                    "user": "U07QCQ3LXDW",
                    "ts": "1234567890.123456",
                },
                {
                    "text": "It's sunny!",
                    "user": "U07QCQ3LXDW",
                    "bot_id": "B07PM4SPSPP",
                    "ts": "1234567890.123457",
                },
                {"text": "Thanks!", "user": "U07QCQ3LXDW", "ts": "1234567890.123458"},
            ]
        }

        mock_client.conversations_replies.return_value = mock_conversation_replies

        result = slack_adapter.get_chat_history(event, mock_client)
        assert result == [
            {"role": "assistant", "content": "It's sunny!"},
            {"role": "user", "content": "Thanks!"},
        ]

    def test_create_webclient_based_on_team_id(self, only_workspace_slack_adapter):
        slack_adapter:SlackAdapter = only_workspace_slack_adapter
        team_id = "T12345678"

        mock_workspace_data = MagicMock()
        mock_workspace_data.access_token = "xoxb-mock-access-token"
        slack_adapter.workspace_data_repository.get_workspace_data_by_team_id.return_value = (
            mock_workspace_data
        )

        web_client = slack_adapter.create_webclient_based_on_team_id(team_id)

        slack_adapter.workspace_data_repository.get_workspace_data_by_team_id.assert_called_once_with(
            team_id=team_id
        )
        assert isinstance(web_client, WebClient)

    def test_create_webclient_based_on_team_id_not_found(self, only_workspace_slack_adapter):
        slack_adapter:SlackAdapter = only_workspace_slack_adapter
        team_id = "T12345678"

        slack_adapter.workspace_data_repository.get_workspace_data_by_team_id.return_value = None

        with pytest.raises(ValueError) as exc_info:
            slack_adapter.create_webclient_based_on_team_id(team_id)

        slack_adapter.workspace_data_repository.get_workspace_data_by_team_id.assert_called_once_with(
            team_id=team_id
        )

        assert f"No workspace data found for team_id {team_id}" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_oauth_redirect(self):
        mock_slack_client = MagicMock()
        mock_slack_client.oauth_v2_access.return_value = {
            "team": {"id": "T12345678"},
            "access_token": "xoxb-mock-token",
        }

        mock_workspace_repository = MagicMock()
        slack_adapter = SlackAdapter(
            app=MagicMock(client=mock_slack_client),
            engine_selector=None,
            bot_service=None,
            reaction_event_repository=None,
            workspace_data_repository=mock_workspace_repository,
            auth_respository=None,
            slack_config=MagicMock(
                slack_client_id="mock-client-id",
                slack_client_secret="mock-client-secret",
            ),
        )

        mock_request = AsyncMock(spec=Request)
        mock_request.query_params = {"code": "mock-auth-code"}

        response = await slack_adapter.oauth_redirect(mock_request)

        mock_slack_client.oauth_v2_access.assert_called_once_with(
            client_id="mock-client-id",
            client_secret="mock-client-secret",
            code="mock-auth-code",
        )
        mock_workspace_repository.create_workspace_data.assert_called_once()
        created_workspace_data = (
            mock_workspace_repository.create_workspace_data.call_args[0][0]
        )

        assert created_workspace_data.team_id == "T12345678"
        assert created_workspace_data.access_token == "xoxb-mock-token"
        assert isinstance(response, RedirectResponse)
