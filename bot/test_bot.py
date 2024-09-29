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
