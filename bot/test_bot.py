from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
import pytest

from .bot import BotCreate, BotUpdate, NameIsRequired, SystemPromptIsRequired, UnsupportedAdapter, UnsupportedModel
from .service import BotServiceV1
from .repository import BotModel, PostgresBotRepository
from .controller import BotControllerV1


# Setup 
TEST_DATABASE_URL = "sqlite:///:memory:"  # Change as needed for your test setup

@pytest.fixture
def session(setup_database):
    """Create a new database session for each test."""
    session_local = sessionmaker(bind=setup_database)
    session = session_local()
    yield session
    session.close()

@pytest.fixture
def setup_repository(session):
    """Set up the repository with the test session."""
    repository = PostgresBotRepository(session=lambda: session)
    return repository

@pytest.fixture
def setup_service(setup_repository):
    """Set up the service with the repository."""
    service = BotServiceV1(setup_repository)
    return service

@pytest.fixture
def setup_controller(setup_service):
    """Set up the controller with the service."""
    controller = BotControllerV1(setup_service)
    return controller

# Tests

class TestBotCreate:
    def test_empty_name(self):
        request = BotCreate(
            name="",
            system_prompt="Non-empty prompt",
            model="OpenAI",
            adapter="Slack"
        )
        with pytest.raises(NameIsRequired):
            request.validate()

    def test_empty_system_prompt(self):
        request = BotCreate(
            name="Customer Report", 
            system_prompt="",
            model="OpenAI",
            adapter="Slack"
        )
        with pytest.raises(SystemPromptIsRequired):
            request.validate()
            
    def test_unsupported_model(self):
        request = BotCreate(
            name="Customer Report", 
            system_prompt="Non-empty prompt", 
            adapter="Slack",
            model="ClosedAI"
        )

        with pytest.raises(UnsupportedModel):
            request.validate()
    
    def test_unsupported_adapter(self):
        request = BotCreate(
            name="Customer Report", 
            system_prompt="Non-empty prompt", 
            adapter="WeChatV2",
            model="OpenAI"
        )

        with pytest.raises(UnsupportedAdapter):
            request.validate()

    def test_create_bot_ok(self):
        tests = [
            {
                "name": "Customer Service",
                "system_prompt": "Non-empty prompt",
                "adapter": "Slack",
                "model": "OpenAI",
            },
        ]

        for test in tests:
            request = BotCreate(**test)
            request.validate()


@pytest.fixture(scope="module")
def setup_database():
    """Create a test database and tables."""
    engine = create_engine(TEST_DATABASE_URL)
    BotModel.metadata.create_all(engine)
    
    yield engine

    BotModel.metadata.drop_all(engine)

class TestUpdateChatbot:
    def test_update_chatbot_success(self, setup_controller):
        
        create_request = BotCreate(
            name="Old Bot",
            system_prompt="Old prompt",
            model="OpenAI",
            adapter="Slack"
        )
        setup_controller.service.create_chatbot(create_request)  # Use the service to create the bot
        created_bot = setup_controller.service.repository.find_bots(0, 10)
        
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

        controller.service.repository.update_bot = lambda bot_id, bot_update: (_ for _ in ()).throw(Exception) 

        with pytest.raises(HTTPException) as exc:
            controller.update_chatbot("some-uuid", bot_update_request)

        assert exc.value.status_code == 500

    def test_update_chatbot_non_existent_bot(self, setup_controller):
        controller = setup_controller

        bot_update_request = BotUpdate(
            name="Updated Bot",
            system_prompt="Updated prompt",
            model="OpenAI",
            adapter="Slack"
        )

        with pytest.raises(HTTPException) as exc:
            controller.update_chatbot(uuid4(), bot_update_request)
        
        assert exc.value.status_code == 400
        assert exc.value.detail == "Bot not found"