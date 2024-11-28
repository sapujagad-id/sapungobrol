import pytest

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from uuid import uuid4
from unittest.mock import patch, MagicMock

from bot.bot import MessageAdapter
from .reaction_event import ReactionEventCreate, Reaction
from .reaction_event_repository import (
    PostgresReactionEventRepository,
    ReactionEventModel,
)

TEST_DATABASE_URL = "sqlite:///:memory:"


class TestReactionEventRepository:
    @pytest.fixture()
    def setup_database(self):
        """Create a test database and tables."""
        engine = create_engine(TEST_DATABASE_URL)
        ReactionEventModel.metadata.create_all(engine)
        yield engine
        ReactionEventModel.metadata.drop_all(engine)

    @pytest.fixture()
    def session(self, setup_database):
        """Create a new database session for each test."""
        session_local = sessionmaker(bind=setup_database, expire_on_commit=False)
        session = session_local()
        yield session
        session.close()

    @pytest.fixture()
    def setup_repository(self, session):
        """Set up the repository with the test session."""
        repository = PostgresReactionEventRepository(session=lambda: session)
        return repository

    def test_create_reaction_event(self, setup_repository):
        repository = setup_repository

        reaction_event_create = ReactionEventCreate(
            bot_id=uuid4(),
            reaction=Reaction.NEGATIVE,
            source_adapter=MessageAdapter.SLACK,
            source_adapter_message_id="123456.7890",
            source_adapter_user_id="U1234567890",
            message="Hi there!",
        )

        repository.create_reaction_event(reaction_event_create)

    def test_delete_reaction_event_existing(self, setup_repository):
        repository = setup_repository

        reaction_event_create = ReactionEventCreate(
            bot_id=uuid4(),
            reaction=Reaction.NEGATIVE,
            source_adapter=MessageAdapter.SLACK,
            source_adapter_message_id="123456.7890",
            source_adapter_user_id="U1234567890",
            message="Hi there!",
        )

        repository.create_reaction_event(reaction_event_create)

        with patch.object(repository, 'create_session') as mock_create_session:
            mock_session = MagicMock()
            mock_create_session.return_value.__enter__.return_value = mock_session

            mock_reaction_event = MagicMock(spec=ReactionEventModel)
            mock_reaction_event.reaction = reaction_event_create.reaction
            mock_reaction_event.source_adapter_message_id = reaction_event_create.source_adapter_message_id
            mock_reaction_event.source_adapter_user_id = reaction_event_create.source_adapter_user_id

            mock_query = mock_session.query.return_value
            mock_filter = mock_query.filter_by.return_value
            mock_filter.first.return_value = mock_reaction_event

            repository.delete_reaction_event(
                reaction=reaction_event_create.reaction,
                source_adapter_message_id=reaction_event_create.source_adapter_message_id,
                source_adapter_user_id=reaction_event_create.source_adapter_user_id,
            )

            mock_session.delete.assert_called_once_with(mock_reaction_event)

            mock_session.commit.assert_called_once()

    def test_delete_reaction_event_nonexistent(self, setup_repository):
        repository = setup_repository

        repository.delete_reaction_event(
            reaction=Reaction.NEGATIVE,
            source_adapter_message_id="nonexistent",
            source_adapter_user_id="U0000000000",
        )

        with repository.create_session() as session:
            reaction_events = session.query(ReactionEventModel).all()
            assert len(reaction_events) == 0
