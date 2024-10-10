from datetime import datetime
from uuid import uuid4
from fastapi import HTTPException
import pytest

from .bot import BotCreate, BotResponse, BotUpdate, MessageAdapter, ModelEngine

class TestBotControllerFetch:
    def test_fetch_chatbots_success(self, setup_controller):
        create_request = BotCreate(
            name="Bot A",
            system_prompt="some system prompt",
            model="OpenAI",
            adapter="Slack"
        )
        setup_controller.create_chatbot(create_request)
        create_request = BotCreate(
            name="Bot B",
            system_prompt="alternative system prompt",
            model="OpenAI",
            adapter="Slack"
        )
        setup_controller.create_chatbot(create_request)
        
        response = setup_controller.fetch_chatbots(skip=0, limit=10)
        assert len(response) == 2
        assert response[0].name == "Bot A"
        assert response[0].model == "OpenAI"
        assert response[1].name == "Bot B"
        assert response[1].system_prompt == "alternative system prompt"

    def test_fetch_chatbots_empty(self, setup_controller):
        response = setup_controller.fetch_chatbots(skip=0, limit=10)
        assert response == []

    def test_fetch_chatbots_pagination(self, setup_controller):
        bot = BotCreate(
            name="Bot Z",
            system_prompt="some very very long Z prompt",
            model="OpenAI",
            adapter="Slack"
        )
        setup_controller.create_chatbot(bot)
        setup_controller.create_chatbot(bot)
        setup_controller.create_chatbot(bot)
        
        response = setup_controller.fetch_chatbots(0, 2)
        assert len(response) == 2
        assert response[0].name == "Bot Z"

class TestBotControllerCreate:
    def test_create_chatbot_success(self, setup_controller):
        create_request = BotCreate(
            name="Bot A",
            system_prompt="some system prompt",
            model="OpenAI",
            adapter="Slack"
        )
        
        response = setup_controller.create_chatbot(create_request)
        assert response == {"detail": "Bot created successfully!"}
        
        bot = setup_controller.service.repository.find_bots(0, 10)
        assert bot[0].name == "Bot A"
        assert bot[0].system_prompt == "some system prompt"
        
    def test_create_chatbot_name_required(self, setup_controller):
        create_request = BotCreate(
            name="",
            system_prompt="some system prompt",
            model="OpenAI",
            adapter="Slack"
        )
        
        with pytest.raises(HTTPException) as exc:
            setup_controller.create_chatbot(create_request)
        
        assert exc.value.status_code == 400
        assert exc.value.detail == "Name is required"
        
    def test_create_chatbot_system_prompt_required(self, setup_controller):
        create_request = BotCreate(
            name="Bot A",
            system_prompt="",
            model="OpenAI",
            adapter="Slack"
        )
        
        with pytest.raises(HTTPException) as exc:
            setup_controller.create_chatbot(create_request)
        
        assert exc.value.status_code == 400
        assert exc.value.detail == "System prompt is required"

    def test_create_chatbot_unsupported_model(self, setup_controller):
        create_request = BotCreate(
            name="Bot A",
            system_prompt="some system prompt",
            model="Llama2.5",
            adapter="Slack"
        )
        
        with pytest.raises(HTTPException) as exc:
            setup_controller.create_chatbot(create_request)
        
        assert exc.value.status_code == 400
        assert exc.value.detail == "Unsupported model"
        
    def test_create_chatbot_unsupported_adapter(self, setup_controller):
        create_request = BotCreate(
            name="Bot A",
            system_prompt="some system prompt",
            model="OpenAI",
            adapter="WeChat"
        )
        
        with pytest.raises(HTTPException) as exc:
            setup_controller.create_chatbot(create_request)
        
        assert exc.value.status_code == 400
        assert exc.value.detail == "Unsupported message adapter"

    def test_create_chatbot_general_exception(self, setup_controller, mocker):
        mocker.patch.object(setup_controller.service, 'create_chatbot', side_effect=Exception)
        
        create_request = BotCreate(
            name="Bot A",
            system_prompt="some system prompt",
            model="OpenAI",
            adapter="Slack"
        )
        
        with pytest.raises(HTTPException) as exc:
            setup_controller.create_chatbot(create_request)
        
        assert exc.value.status_code == 500
        assert exc.value.detail == "Something went wrong"

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
        
    def test_update_chatbot_slug_required(self, setup_controller):
        controller = setup_controller

        bot_update_request = BotUpdate(
            name="Bot A",
            system_prompt="Updated prompt",
            model="OpenAI",
            adapter="Slack",
            slug=""  
        )

        with pytest.raises(HTTPException) as exc:
            controller.update_chatbot(uuid4(), bot_update_request)
        
        assert exc.value.status_code == 400
        assert exc.value.detail == "Slug is required"