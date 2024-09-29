import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from bot.bot import BotCreate, BotUpdate
from bot.repository import BotModel, PostgresBotRepository

# Setup 
TEST_DATABASE_URL = "sqlite:///:memory:"  # Using an in-memory SQLite database for testing purposes.

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
    SessionLocal = sessionmaker(
      expire_on_commit = False, # to prevent unbound/detached session error
      bind = setup_database
    )
    session = SessionLocal()
    yield session
    session.close()

@pytest.fixture
def repository(session):
    """Fixture for PostgresBotRepository using the test session."""
    return PostgresBotRepository(session=lambda: session)

@pytest.fixture
def bot_create_data():
    """Fixture to create a BotCreate object for testing."""
    return BotCreate(
        name="Test Bot",
        system_prompt="This is a test system prompt",
        model="OpenAI",
        adapter="Slack"
    )

@pytest.fixture
def bot_update_data():
    """Fixture to create a BotUpdate object for testing updates."""
    return BotUpdate(
        name="Updated Test Bot",
        system_prompt="This is an updated test system prompt",
        model="OpenAI",
        adapter="Slack"
    )

class TestBotRepository:
  def test_create_bot(self, repository, bot_create_data):
      repository.create_bot(bot_create_data)
      bots = repository.find_bots(skip=0, limit=10)
      
      assert len(bots) == 1
      assert bots[0].name == bot_create_data.name
      assert bots[0].system_prompt == bot_create_data.system_prompt

  def test_find_bot_by_id(self, repository, bot_create_data):
      repository.create_bot(bot_create_data)
      bots = repository.find_bots(skip=0, limit=10)
      bot_id = bots[0].id

      found_bot = repository.find_bot_by_id(bot_id)
      assert found_bot is not None
      assert found_bot.id == bot_id

  def test_update_bot(self, repository, bot_create_data, bot_update_data):
      repository.create_bot(bot_create_data)
      bots = repository.find_bots(skip=0, limit=10)
      bot = bots[0]

      updated_bot = repository.update_bot(bot, bot_update_data)
      assert updated_bot.name == bot_update_data.name
      assert updated_bot.system_prompt == bot_update_data.system_prompt

  def test_find_bots(self, repository, bot_create_data):
      # Create multiple bots
      for _ in range(3):
          repository.create_bot(bot_create_data)
      
      bots = repository.find_bots(skip=0, limit=2)
      assert len(bots) == 2

  def test_find_non_existent_bot(self, repository):
      non_existent_bot_id = uuid4()
      bot = repository.find_bot_by_id(non_existent_bot_id)
      assert bot is None