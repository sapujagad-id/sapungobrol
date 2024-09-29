from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException
import pytest

from .bot import BotCreate, BotNotFound, BotUpdate, NameIsRequired, SystemPromptIsRequired, UnsupportedAdapter, UnsupportedModel
from .service import BotService, BotServiceV1
from .repository import BotModel, PostgresBotRepository
from .controller import BotControllerV1

TEST_DATABASE_URL = "sqlite:///:memory:"

@pytest.fixture(scope="module")
def setup_database():
    """Create a test database and tables."""
    engine = create_engine(TEST_DATABASE_URL)
    BotModel.metadata.create_all(engine)
    
    yield engine

    BotModel.metadata.drop_all(engine)
    
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

        with pytest.raises(NameIsRequired) as exc:
            setup_service.update_chatbot(uuid4(), bot_update_request)
        
        assert exc.typename == "NameIsRequired"
        
    def test_update_chatbot_system_prompt_required(self, setup_service: BotService):
        bot_update_request = BotUpdate(
            name="Updated Bot",
            system_prompt="",
            model="OpenAI",
            adapter="Slack"
        )

        with pytest.raises(SystemPromptIsRequired) as exc:
            setup_service.update_chatbot(uuid4(), bot_update_request)
        
        assert exc.typename == "SystemPromptIsRequired"
        
    def test_update_chatbot_unsupported_model(self, setup_service: BotService):
        bot_update_request = BotUpdate(
            name="Updated Bot",
            system_prompt="Updated prompt",
            model="UnsupportedModel",
            adapter="Slack"
        )

        with pytest.raises(UnsupportedModel) as exc:
            setup_service.update_chatbot(uuid4(), bot_update_request)
        
        assert exc.typename == "UnsupportedModel"

    def test_update_chatbot_unsupported_adapter(self, setup_service: BotService):
        bot_update_request = BotUpdate(
            name="Updated Bot",
            system_prompt="Updated prompt",
            model="OpenAI",
            adapter="UnsupportedAdapter"
        )

        with pytest.raises(UnsupportedAdapter) as exc:
            setup_service.update_chatbot(uuid4(), bot_update_request)
        
        assert exc.typename == "UnsupportedAdapter"
        
    def test_update_chatbot_not_found(self, setup_service: BotService):
        bot_update_request = BotUpdate(
            name="Updated Bot",
            system_prompt="Updated prompt",
            model="OpenAI",
            adapter="Slack"
        )

        with pytest.raises(BotNotFound) as exc:
            setup_service.update_chatbot(uuid4(), bot_update_request)

        assert exc.typename == "BotNotFound"
