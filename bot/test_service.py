from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
import pytest

from .bot import BotCreate, BotNotFound, BotUpdate, NameIsRequired, SlugIsRequired, SystemPromptIsRequired, UnsupportedAdapter, UnsupportedModel
from .service import BotService, BotServiceV1
from .repository import BotModel, PostgresBotRepository
from .controller import BotControllerV1

class TestBotServiceGetBotById:
    def test_find_bot_by_id_success(self, setup_service: BotService):
        create_request = BotCreate(
            name="Test Bot",
            system_prompt="Test prompt",
            model="OpenAI",
            adapter="Slack"
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

    def test_find_bot_by_id_not_found(self, setup_service: BotService):
        bot = setup_service.get_chatbot_by_id(uuid4())
        assert bot == None

class TestBotServiceUpdate:
    def test_update_chatbot_success(self, setup_service: BotService):
        create_request = BotCreate(
            name="Old Bot",
            system_prompt="Old prompt",
            model="OpenAI",
            adapter="Slack"
        )
        
        setup_service.create_chatbot(create_request)
        bots = setup_service.get_chatbots(0, 10)
        
        bot_update_request = BotUpdate(
            name="Updated Bot",
            system_prompt="Updated prompt",
            model="OpenAI",
            adapter="Slack"
        )
        setup_service.update_chatbot(bots[0].id, bot_update_request)

        updated_bot = setup_service.repository.find_bots(0, 10)
        assert updated_bot[0].name == "Updated Bot"
        assert updated_bot[0].system_prompt == "Updated prompt"
        
    def test_update_chatbot_name_required(self, setup_service: BotService):
        bot_update_request = BotUpdate(
            name="",
            system_prompt="Updated prompt",
            model="OpenAI",
            adapter="Slack"
        )

        with pytest.raises(NameIsRequired):
            setup_service.update_chatbot(uuid4(), bot_update_request)
        
    def test_update_chatbot_system_prompt_required(self, setup_service: BotService):
        bot_update_request = BotUpdate(
            name="Updated Bot",
            system_prompt="",
            model="OpenAI",
            adapter="Slack"
        )

        with pytest.raises(SystemPromptIsRequired):
            setup_service.update_chatbot(uuid4(), bot_update_request)
        
    def test_update_chatbot_unsupported_model(self, setup_service: BotService):
        bot_update_request = BotUpdate(
            name="Updated Bot",
            system_prompt="Updated prompt",
            model="UnsupportedModel",
            adapter="Slack"
        )

        with pytest.raises(UnsupportedModel):
            setup_service.update_chatbot(uuid4(), bot_update_request)

    def test_update_chatbot_unsupported_adapter(self, setup_service: BotService):
        bot_update_request = BotUpdate(
            name="Updated Bot",
            system_prompt="Updated prompt",
            model="OpenAI",
            adapter="UnsupportedAdapter"
        )

        with pytest.raises(UnsupportedAdapter):
            setup_service.update_chatbot(uuid4(), bot_update_request)
        
    def test_update_chatbot_not_found(self, setup_service: BotService):
        bot_update_request = BotUpdate(
            name="Updated Bot",
            system_prompt="Updated prompt",
            model="OpenAI",
            adapter="Slack"
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