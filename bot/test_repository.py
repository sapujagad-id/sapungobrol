import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4

from bot.bot import BotCreate, BotUpdate
from bot.repository import BotModel, PostgresBotRepository

@pytest.fixture
def bot_create_data():
    """Fixture to create a BotCreate object for testing."""
    return BotCreate(
        name="Test Bot",
        system_prompt="This is a test system prompt",
        model="OpenAI",
        adapter="Slack",
        slug="test-bot"  # Added slug
    )

@pytest.fixture
def bot_update_data():
    """Fixture to create a BotUpdate object for testing updates."""
    return BotUpdate(
        name="Updated Test Bot",
        system_prompt="This is an updated test system prompt",
        model="OpenAI",
        adapter="Slack",
        slug="updated-test-bot"  # Added slug
    )

class TestBotRepository:
    def test_create_bot(self, setup_repository, bot_create_data):
        setup_repository.create_bot(bot_create_data)
        bots = setup_repository.find_bots(skip=0, limit=10)
        
        assert len(bots) == 1
        assert bots[0].name == bot_create_data.name
        assert bots[0].system_prompt == bot_create_data.system_prompt
        assert bots[0].slug == bot_create_data.slug  # Check slug

    def test_find_bot_by_id(self, setup_repository, bot_create_data):
        setup_repository.create_bot(bot_create_data)
        bots = setup_repository.find_bots(skip=0, limit=10)
        bot_id = bots[0].id

        found_bot = setup_repository.find_bot_by_id(bot_id)
        assert found_bot is not None
        assert found_bot.id == bot_id
        assert found_bot.slug == bot_create_data.slug  # Check slug

    def test_update_bot(self, setup_repository, bot_create_data, bot_update_data):
        setup_repository.create_bot(bot_create_data)
        bots = setup_repository.find_bots(skip=0, limit=10)
        bot = bots[0]

        updated_bot = setup_repository.update_bot(bot, bot_update_data)
        assert updated_bot.name == bot_update_data.name
        assert updated_bot.system_prompt == bot_update_data.system_prompt
        assert updated_bot.slug == bot_update_data.slug  # Check slug
    
    def test_delete_bot(self, setup_repository, bot_create_data):
        setup_repository.create_bot(bot_create_data)
        bots = setup_repository.find_bots(skip=0, limit=10)
        bot = bots[0]

        setup_repository.delete_bot(bot)
        assert len(setup_repository.find_bots(skip=0, limit=10)) == 0

    def test_find_bots(self, setup_repository, bot_create_data):
        # Create multiple bots
        for i in range(3):
            bot_create_data.slug = f"test-bot-{i}"
            setup_repository.create_bot(bot_create_data)
        
        bots = setup_repository.find_bots(skip=0, limit=2)
        assert len(bots) == 2

    def test_find_non_existent_bot(self, setup_repository):
        non_existent_bot_id = uuid4()
        bot = setup_repository.find_bot_by_id(non_existent_bot_id)
        assert bot is None
