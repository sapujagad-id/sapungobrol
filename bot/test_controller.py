from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
import pytest

from .bot import BotCreate, BotUpdate, NameIsRequired, SystemPromptIsRequired, UnsupportedAdapter, UnsupportedModel
from .service import BotServiceV1
from .repository import BotModel, PostgresBotRepository
from .controller import BotControllerV1

class TestBotControllerCreate:
    pass

class TestBotControllerUpdate:
    def test_update_chatbot_success(self, setup_controller):
        create_request = BotCreate(
            name="Old Bot",
            system_prompt="Old prompt",
            model="OpenAI",
            adapter="Slack"
        )
        
        setup_controller.create_chatbot(create_request)
        created_bot = setup_controller.fetch_chatbots(0, 10)
        
        bot_update_request = BotUpdate(
            name="Updated Bot",
            system_prompt="Updated prompt",
            model="OpenAI",
            adapter="Slack"
        )
        response = setup_controller.update_chatbot(created_bot[0].id, bot_update_request)
        assert response == {"detail": "Bot updated successfully!"}

        updated_bot = setup_controller.service.repository.find_bots(0, 10)
        assert updated_bot[0].name == "Updated Bot"
        assert updated_bot[0].system_prompt == "Updated prompt"
        
    def test_update_chatbot_name_required(self, setup_controller):
        controller = setup_controller

        bot_update_request = BotUpdate(
            name="",
            system_prompt="Updated prompt",
            model="OpenAI",
            adapter="Slack"
        )

        with pytest.raises(HTTPException) as exc:
            controller.update_chatbot(uuid4(), bot_update_request)
        
        assert exc.value.status_code == 400
        assert exc.value.detail == "Name is required"
        
    def test_update_chatbot_system_prompt_required(self, setup_controller):
        controller = setup_controller

        bot_update_request = BotUpdate(
            name="Updated Bot",
            system_prompt="",
            model="OpenAI",
            adapter="Slack"
        )

        with pytest.raises(HTTPException) as exc:
            controller.update_chatbot(uuid4(), bot_update_request)
        
        assert exc.value.status_code == 400
        assert exc.value.detail == "System prompt is required"
        
    def test_update_chatbot_unsupported_model(self, setup_controller):
        controller = setup_controller

        bot_update_request = BotUpdate(
            name="Updated Bot",
            system_prompt="Updated prompt",
            model="UnsupportedModel",
            adapter="Slack"
        )

        with pytest.raises(HTTPException) as exc:
            controller.update_chatbot(uuid4(), bot_update_request)
        
        assert exc.value.status_code == 400
        assert exc.value.detail == "Unsupported model"

    def test_update_chatbot_unsupported_adapter(self, setup_controller):
        controller = setup_controller

        bot_update_request = BotUpdate(
            name="Updated Bot",
            system_prompt="Updated prompt",
            model="OpenAI",
            adapter="UnsupportedAdapter"
        )

        with pytest.raises(HTTPException) as exc:
            controller.update_chatbot(uuid4(), bot_update_request)

        assert exc.value.status_code == 400
        assert exc.value.detail == "Unsupported message adapter"
        
    def test_update_chatbot_general_exception(self, setup_controller):
        controller = setup_controller

        bot_update_request = BotUpdate(
            name="Updated Bot",
            system_prompt="Updated prompt",
            model="OpenAI",
            adapter="Slack"
        )

        with pytest.raises(HTTPException) as exc:
            controller.update_chatbot("some-uuid", bot_update_request)

        assert exc.value.status_code == 500
