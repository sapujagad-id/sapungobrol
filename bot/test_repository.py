import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4
from unittest.mock import MagicMock, patch

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
    
    def test_get_dashboard_data(self, setup_repository, bot_create_data):
        mock_bot_id = uuid4()

        mock_session = MagicMock() 
        setup_repository.create_session = MagicMock()
        setup_repository.create_session.return_value.__enter__.return_value = mock_session

        mock_last_threads = [
            ("message1", 3),
            ("message2", 5),
        ]

        mock_cumulative_threads = 10

        mock_session.query.return_value.filter.return_value.group_by.return_value.limit.return_value.all.return_value = mock_last_threads
        mock_session.query.return_value.filter.return_value.scalar.return_value = mock_cumulative_threads

        result = setup_repository.get_dashboard_data(mock_bot_id)

        assert "last_threads" in result
        assert "cumulative_threads" in result
        assert len(result["last_threads"]) == len(mock_last_threads)
        assert result["cumulative_threads"] == mock_cumulative_threads

    def test_get_dashboard_data_no_threads(self, setup_repository):
        mock_bot_id = uuid4()

        mock_session = MagicMock()
        setup_repository.create_session = MagicMock()
        setup_repository.create_session.return_value.__enter__.return_value = mock_session

        mock_session.query.return_value.filter.return_value.group_by.return_value.limit.return_value.all.return_value = []
        mock_session.query.return_value.filter.return_value.scalar.return_value = 0

        result = setup_repository.get_dashboard_data(mock_bot_id)

        assert result["last_threads"] == []
        assert result["cumulative_threads"] == 0
        
    def test_get_dashboard_data_with_exception(self, setup_repository):
        mock_bot_id = uuid4()

        mock_session = MagicMock()
        setup_repository.create_session = MagicMock()
        setup_repository.create_session.return_value.__enter__.return_value = mock_session

        with patch.object(setup_repository, 'logger') as mock_logger:
            mock_session.query.side_effect = Exception("Simulated database error")

            with pytest.raises(Exception, match="Simulated database error"):
                setup_repository.get_dashboard_data(mock_bot_id)

            mock_logger.error.assert_called_once_with(
                f"Error in get_dashboard_data for bot_id: {mock_bot_id}. Error: Simulated database error"
            )