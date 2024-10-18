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
            adapter="Slack",
            slug="bot-a"  # Added slug
        )
        setup_controller.create_chatbot(create_request)
        
        create_request = BotCreate(
            name="Bot B",
            system_prompt="alternative system prompt",
            model="OpenAI",
            adapter="Slack",
            slug="bot-b"  # Added slug
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
            adapter="Slack",
            slug="bot-z"  # Added slug
        )
        for i in range(3):
            bot.slug = f"bot-{i}"
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
            adapter="Slack",
            slug="bot-a"  # Added slug
        )
        
        response = setup_controller.create_chatbot(create_request)
        assert response == {"detail": "Bot created successfully!"}
        
        bot = setup_controller.service.repository.find_bots(0, 10)
        assert bot[0].name == "Bot A"
        assert bot[0].system_prompt == "some system prompt"
        assert bot[0].slug == "bot-a"  # Check slug

    def test_create_chatbot_slug_exist(self, setup_controller):
        create_request = BotCreate(
            name="Bot A",
            system_prompt="some system prompt",
            model="OpenAI",
            adapter="Slack",
            slug="bot-a"  
        )

        create_request_1 = BotCreate(
            name="Bot AB",
            system_prompt="some system prompt",
            model="OpenAI",
            adapter="Slack",
            slug="bot-a"  
        )
        
        setup_controller.create_chatbot(create_request)
        with pytest.raises(HTTPException) as exc:
            setup_controller.create_chatbot(create_request_1)
        
        assert exc.value.status_code == 400
        assert exc.value.detail == "Slug is exist"

    def test_create_chatbot_name_required(self, setup_controller):
        create_request = BotCreate(
            name="",
            system_prompt="some system prompt",
            model="OpenAI",
            adapter="Slack",
            slug="bot-a"  # Added slug
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
            adapter="Slack",
            slug="bot-a"  # Added slug
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
            adapter="Slack",
            slug="bot-a"  # Added slug
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
            adapter="WeChat",
            slug="bot-a"  # Added slug
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
            adapter="Slack",
            slug="bot-a"  # Added slug
        )
        
        with pytest.raises(HTTPException) as exc:
            setup_controller.create_chatbot(create_request)
        
        assert exc.value.status_code == 500
        assert exc.value.detail == "Something went wrong"

    def test_create_chatbot_slug_required(self, setup_controller):
        create_request = BotCreate(
            name="Bot A",
            system_prompt="some system prompt",
            model="OpenAI",
            adapter="Slack",
            slug=""  
        )
        
        with pytest.raises(HTTPException) as exc:
            setup_controller.create_chatbot(create_request)
        
        
        assert exc.value.status_code == 400
        assert exc.value.detail == "Slug is required"

class TestBotControllerUpdate:
    def test_update_chatbot_success(self, setup_controller):
        create_request = BotCreate(
            name="Old Bot",
            system_prompt="Old prompt",
            model="OpenAI",
            adapter="Slack",
            slug="old-bot"  # Added slug
        )
        
        setup_controller.create_chatbot(create_request)
        created_bot = setup_controller.fetch_chatbots(0, 10)
        
        bot_update_request = BotUpdate(
            name="Updated Bot",
            system_prompt="Updated prompt",
            model="OpenAI",
            adapter="Slack",
            slug="updated-bot"  # Added slug
        )
        response = setup_controller.update_chatbot(created_bot[0].id, bot_update_request)
        assert response == {"detail": "Bot updated successfully!"}

        updated_bot = setup_controller.service.repository.find_bots(0, 10)
        assert updated_bot[0].name == "Updated Bot"
        assert updated_bot[0].system_prompt == "Updated prompt"
        assert updated_bot[0].slug == "updated-bot"  # Check slug

    def test_update_chatbot_slug_exist(self, setup_controller):
        controller = setup_controller

        
        create_request = BotCreate(
            name="Test Bot 1",
            system_prompt="Test prompt",
            model="OpenAI",
            adapter="Slack",
            slug="existing-slug"  
        )
        create_request2 = BotCreate(
            name="Test Bot 2",
            system_prompt="Test prompt",
            model="OpenAI",
            adapter="Slack",
            slug="existing-slug-1"  
        )
        controller.create_chatbot(create_request)  
        controller.create_chatbot(create_request2)  

        created_bot = setup_controller.fetch_chatbots(0, 10)

        
        bot_update_request = BotUpdate(
            name="Updated Bot",
            system_prompt="Updated prompt",
            model="OpenAI",
            adapter="Slack",
            slug="existing-slug-1" 
        )

        with pytest.raises(HTTPException) as exc:
            controller.update_chatbot(created_bot[0].id, bot_update_request)

        assert exc.value.status_code == 400
        assert exc.value.detail == "Slug is exist"
        
    def test_update_chatbot_name_required(self, setup_controller):
        controller = setup_controller

        bot_update_request = BotUpdate(
            name="",
            system_prompt="Updated prompt",
            model="OpenAI",
            adapter="Slack",
            slug="updated-bot"  # Added slug
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
            adapter="Slack",
            slug="updated-bot"  # Added slug
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
            adapter="Slack",
            slug="updated-bot"  # Added slug
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
            adapter="UnsupportedAdapter",
            slug="updated-bot"  # Added slug
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
            adapter="Slack",
            slug="updated-bot"  # Added slug
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

class TestBotControllerCheckSlugExist:
    def test_check_slug_exist_success(self, setup_controller):
        slug = "existing-slug"
        
        setup_controller.service.is_slug_exist = lambda x: True  

        response = setup_controller.check_slug_exist(slug)

        assert response == {"detail": True}  

    def test_check_slug_exist_not_found(self, setup_controller):
        slug = "non-existent-slug"
        
        setup_controller.service.is_slug_exist = lambda x: False  

        response = setup_controller.check_slug_exist(slug)

        assert response == {"detail": False}  

    
