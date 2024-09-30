# Configurations for all tests in bot module

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest

from .service import BotServiceV1
from .repository import BotModel, PostgresBotRepository
from .controller import BotControllerV1

TEST_DATABASE_URL = "sqlite:///:memory:"  # Change as needed for your test setup

@pytest.fixture(scope="module")
def session(setup_database):
    """Create a new database session for each test."""
    session_local = sessionmaker(
        bind=setup_database, 
        expire_on_commit=False
    )
    session = session_local()
    yield session
    session.close()

@pytest.fixture(scope="module")
def setup_repository(session):
    """Set up the repository with the test session."""
    repository = PostgresBotRepository(session=lambda: session)
    return repository

@pytest.fixture(scope="module")
def setup_service(setup_repository):
    """Set up the service with the repository."""
    service = BotServiceV1(setup_repository)
    return service

@pytest.fixture(scope="module")
def setup_controller(setup_service):
    """Set up the controller with the service."""
    controller = BotControllerV1(setup_service)
    return controller

@pytest.fixture(scope="module")
def setup_database():
    """Create a test database and tables."""
    engine = create_engine(TEST_DATABASE_URL)
    BotModel.metadata.create_all(engine)
    yield engine
    BotModel.metadata.drop_all(engine)