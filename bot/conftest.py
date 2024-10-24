# Configurations for all tests in bot module

from datetime import datetime
from unittest.mock import Mock
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

from auth.controller import AuthControllerV1
from auth.dto import ProfileResponse
from bot.bot import BotResponse, MessageAdapter, ModelEngine
from bot.helper import relative_time
from bot.view import BotViewV1

from .service import BotServiceV1
from .repository import BotModel, PostgresBotRepository
from .controller import BotControllerV1

TEST_DATABASE_URL = "sqlite:///:memory:"  # Change as needed for your test setu

@pytest.fixture()
def session(setup_database):
    """Create a new database session for each test."""
    session_local = sessionmaker(
        bind=setup_database, 
        expire_on_commit=False
    )
    session = session_local()
    yield session
    session.close()

@pytest.fixture()
def setup_repository(session):
    """Set up the repository with the test session."""
    repository = PostgresBotRepository(session=lambda: session)
    return repository

@pytest.fixture()
def setup_service(setup_repository):
    """Set up the service with the repository."""
    service = BotServiceV1(setup_repository)
    return service

@pytest.fixture()
def setup_controller(setup_service):
    """Set up the controller with the service."""
    controller = BotControllerV1(setup_service)
    return controller

@pytest.fixture()
def setup_database():
    """Create a test database and tables."""
    engine = create_engine(TEST_DATABASE_URL)
    BotModel.metadata.create_all(engine)
    yield engine
    BotModel.metadata.drop_all(engine)

@pytest.fixture()
def setup_jwt_secret():
    """Set up a mock JWT secret."""
    return "some_arbitrary_string_here"

@pytest.fixture()
def dummy_user_profile():
    """Return a mock user profile."""
    return ProfileResponse(data={
        "id": str(uuid4()),  # Replace with actual fields expected by User
        "email": "test@broom.id",
        "created_at": "2024-10-24T00:00:00Z",
        # Include other necessary fields...
    })

@pytest.fixture()
def setup_view(setup_controller, setup_service):
    """Setup the BotViewV1 with mocked controller and service."""
    mock_controller = Mock(spec=AuthControllerV1)
    view = BotViewV1(mock_controller, setup_service, setup_controller)
    view.auth_controller = mock_controller
    return view
    
@pytest.fixture
def setup_bots():
  '''Setup BotResponse list for template context'''
  return [
    BotResponse(
        id = uuid4(),
        name = "Bot A",
        system_prompt = "prompt A here",
        model = ModelEngine.OPENAI,
        adapter = MessageAdapter.SLACK,
        created_at = datetime.fromisocalendar(2024, 1, 1),
        updated_at = datetime.fromisocalendar(2024, 1, 1),
        updated_at_relative = relative_time(datetime.fromisocalendar(2024, 1, 1)),
    ),
    BotResponse(
        id = uuid4(),
        name = "Bot B",
        system_prompt = "a much longer prompt B here",
        model = ModelEngine.OPENAI,
        adapter = MessageAdapter.SLACK,
        created_at = datetime.now(),
        updated_at = datetime.now(),
        updated_at_relative = relative_time(datetime.now()),
    )
  ]