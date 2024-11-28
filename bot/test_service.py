from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
import pytest

from .bot import BotCreate, BotNotFound, BotUpdate, NameIsRequired, SlugIsExist, SlugIsRequired, SystemPromptIsRequired, UnsupportedAdapter, UnsupportedModel
from .service import BotService, BotServiceV1
from .repository import BotModel, PostgresBotRepository
from .controller import BotControllerV1
from unittest.mock import MagicMock

class TestBotServiceGetBotById:
    def test_find_bot_by_id_success(self, setup_service: BotService):
        create_request = BotCreate(
            name="Test Bot",
            system_prompt="Test prompt",
            model="OpenAI",
            adapter="Slack",
            slug="test-bot"  # Added slug
        )
        
        setup_service.create_chatbot(create_request)

        bots = setup_service.get_chatbots(0, 10)
        bot_id = bots[0].id
        found_bot = setup_service.get_chatbot_by_id(bot_id)

        assert found_bot is not None
        assert found_bot.name == create_request.name
        assert found_bot.system_prompt == create_request.system_prompt
        assert found_bot.model == create_request.model
        assert found_bot.adapter == create_request.adapter
        assert found_bot.slug == create_request.slug  # Check slug

    def test_find_bot_by_id_not_found(self, setup_service: BotService):
        bot = setup_service.get_chatbot_by_id(uuid4())
        assert bot == None

class TestBotServiceGetBotBySlug:
    def test_find_bot_by_slug_success(self, setup_service: BotService):
        create_request = BotCreate(
            name="Test Bot",
            system_prompt="Test prompt",
            model="OpenAI",
            adapter="Slack",
            slug="test-bot"  # Use a specific slug
        )
        
        setup_service.create_chatbot(create_request)

        found_bot = setup_service.get_chatbot_by_slug("test-bot")  # Call the new method

        assert found_bot is not None
        assert found_bot.name == create_request.name
        assert found_bot.system_prompt == create_request.system_prompt
        assert found_bot.model == create_request.model
        assert found_bot.adapter == create_request.adapter
        assert found_bot.slug == create_request.slug  # Check slug

    def test_find_bot_by_slug_not_found(self, setup_service: BotService):
        bot = setup_service.get_chatbot_by_slug("non-existent-slug")
        assert bot is None

    def test_is_slug_exist_success(self, setup_service: BotService):
        create_request = BotCreate(
            name="Test Bot",
            system_prompt="Test prompt",
            model="OpenAI",
            adapter="Slack",
            slug="test-bot"  # Use a specific slug
        )
        
        # Create a bot to ensure the slug exists
        setup_service.create_chatbot(create_request)

        # Now check if the slug exists
        exists = setup_service.is_slug_exist("test-bot")
        assert exists is True

    def test_is_slug_exist_not_found(self, setup_service: BotService):
        # Check a slug that doesn't exist
        exists = setup_service.is_slug_exist("non-existent-slug")
        assert exists is False

    def test_is_slug_exist_error_handling(self, mocker, setup_service: BotService):
        # Mock the repository method to raise an exception
        mocker.patch.object(setup_service.repository, 'find_bot_by_slug', side_effect=Exception("Database error"))

        exists = setup_service.is_slug_exist("error-prone-slug")
        assert exists is False

class TestBotServiceCreate:
    def test_create_chatbot_slug_failed(self, setup_service: BotService):
        create_request1 = BotCreate(
            name="First Bot",
            system_prompt="First prompt",
            model="OpenAI",
            adapter="Slack",
            slug="unique-bot"
        )
        
        setup_service.create_chatbot(create_request1)

        create_request2 = BotCreate(
            name="Second Bot",
            system_prompt="Second prompt",
            model="OpenAI",
            adapter="Slack",
            slug="unique-bot"  # Attempt to create with the same slug
        )

        with pytest.raises(SlugIsExist):
            setup_service.create_chatbot(create_request2)

class TestBotServiceUpdate:
    def test_update_chatbot_success(self, setup_service: BotService):
        create_request = BotCreate(
            name="Old Bot",
            system_prompt="Old prompt",
            model="OpenAI",
            adapter="Slack",
            slug="old-bot"  # Added slug
        )
        
        setup_service.create_chatbot(create_request)
        bots = setup_service.get_chatbots(0, 10)
        
        bot_update_request = BotUpdate(
            name="Updated Bot",
            system_prompt="Updated prompt",
            model="OpenAI",
            adapter="Slack",
            slug="updated-bot"  # Added slug
        )
        setup_service.update_chatbot(bots[0].id, bot_update_request)

        updated_bot = setup_service.repository.find_bots(0, 10)
        assert updated_bot[0].name == "Updated Bot"
        assert updated_bot[0].system_prompt == "Updated prompt"
        assert updated_bot[0].slug == "updated-bot"  # Check slug
        
    def test_update_chatbot_name_required(self, setup_service: BotService):
        bot_update_request = BotUpdate(
            name="",
            system_prompt="Updated prompt",
            model="OpenAI",
            adapter="Slack",
            slug="updated-bot"  # Added slug
        )

        with pytest.raises(NameIsRequired):
            setup_service.update_chatbot(uuid4(), bot_update_request)
        
    def test_update_chatbot_system_prompt_required(self, setup_service: BotService):
        bot_update_request = BotUpdate(
            name="Updated Bot",
            system_prompt="",
            model="OpenAI",
            adapter="Slack",
            slug="updated-bot"  # Added slug
        )

        with pytest.raises(SystemPromptIsRequired):
            setup_service.update_chatbot(uuid4(), bot_update_request)
        
    def test_update_chatbot_unsupported_model(self, setup_service: BotService):
        bot_update_request = BotUpdate(
            name="Updated Bot",
            system_prompt="Updated prompt",
            model="UnsupportedModel",
            adapter="Slack",
            slug="updated-bot"  # Added slug
        )

        with pytest.raises(UnsupportedModel):
            setup_service.update_chatbot(uuid4(), bot_update_request)

    def test_update_chatbot_unsupported_adapter(self, setup_service: BotService):
        bot_update_request = BotUpdate(
            name="Updated Bot",
            system_prompt="Updated prompt",
            model="OpenAI",
            adapter="UnsupportedAdapter",
            slug="updated-bot"  # Added slug
        )

        with pytest.raises(UnsupportedAdapter):
            setup_service.update_chatbot(uuid4(), bot_update_request)
        
    def test_update_chatbot_not_found(self, setup_service: BotService):
        bot_update_request = BotUpdate(
            name="Updated Bot",
            system_prompt="Updated prompt",
            model="OpenAI",
            adapter="Slack",
            slug="updated-bot"  # Added slug
        )

        with pytest.raises(BotNotFound):
            setup_service.update_chatbot(uuid4(), bot_update_request)

    def test_update_chatbot_slug_required(self, setup_service: BotService):
        bot_update_request = BotUpdate(
            name="Updated Bot",
            system_prompt="Halo",
            model="OpenAI",
            adapter="Slack",
            slug =""
        )

        with pytest.raises(SlugIsRequired):
            setup_service.update_chatbot(uuid4(), bot_update_request)

class TestBotServiceDelete:
    def test_delete_chatbot_success(self, setup_service: BotService):
        create_request = BotCreate(
            name="Bot",
            system_prompt="prompt",
            model="OpenAI",
            adapter="Slack",
            slug="bot"  # Added slug
        )
        
        setup_service.create_chatbot(create_request)
        bots = setup_service.get_chatbots(0, 10)
        
        setup_service.delete_chatbot(bots[0].id)

        assert len(setup_service.repository.find_bots(0, 10)) == 0
        
    def test_delete_chatbot_not_found(self, setup_service: BotService):
        with pytest.raises(BotNotFound):
            setup_service.delete_chatbot(uuid4())
            
class TestBotServiceDashboardData:
    def test_get_dashboard_data_success(self, setup_service):
        mock_bot_id = uuid4()

        mock_dashboard_data = {
            "last_threads": [
                {"thread": "message1", "negative_count": 3},
                {"thread": "message2", "negative_count": 5},
            ],
            "cumulative_threads": 10,
        }

        setup_service.repository.get_dashboard_data = MagicMock(return_value=mock_dashboard_data)

        result = setup_service.get_dashboard_data(mock_bot_id)

        assert "last_threads" in result
        assert "cumulative_threads" in result
        assert len(result["last_threads"]) == 2
        assert result["cumulative_threads"] == 10

    def test_get_dashboard_data_no_threads(self, setup_service):
        mock_bot_id = uuid4()

        mock_dashboard_data = {
            "last_threads": [],
            "cumulative_threads": 0,
        }

        setup_service.repository.get_dashboard_data = MagicMock(return_value=mock_dashboard_data)

        result = setup_service.get_dashboard_data(mock_bot_id)

        assert result["last_threads"] == []
        assert result["cumulative_threads"] == 0

    def test_get_dashboard_data_error_handling(self, mocker, setup_service):
        mock_bot_id = uuid4()

        mocker.patch.object(setup_service.repository, 'get_dashboard_data', side_effect=Exception("Database error"))

        try:
            setup_service.get_dashboard_data(mock_bot_id)
        except Exception as e:
            assert str(e) == "Database error"