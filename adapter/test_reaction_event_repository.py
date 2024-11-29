import pytest

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from uuid import uuid4

from bot.bot import MessageAdapter
from .reaction_event import ReactionEventCreate, Reaction
from .reaction_event_repository import (
    PostgresReactionEventRepository,
    ReactionEventModel,
)

TEST_DATABASE_URL = "sqlite:///:memory:"


class TestReactionEventRepository:
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

    def test_fetch_reaction_event_by_bot_id(self, setup_repository):
        repository = setup_repository
        bot_id = uuid4()

        # Add test data
        events = [
            ReactionEventCreate(
                bot_id=bot_id,
                reaction=Reaction.NEGATIVE,
                source_adapter=MessageAdapter.SLACK,
                source_adapter_message_id="conv1",
                source_adapter_user_id="U123",
                message="Negative feedback",
            ),
            ReactionEventCreate(
                bot_id=bot_id,
                reaction=Reaction.NEGATIVE,
                source_adapter=MessageAdapter.SLACK,
                source_adapter_message_id="conv1",
                source_adapter_user_id="U124",
                message="Another negative feedback",
            ),
            ReactionEventCreate(
                bot_id=bot_id,
                reaction=Reaction.POSITIVE,
                source_adapter=MessageAdapter.SLACK,
                source_adapter_message_id="conv2",
                source_adapter_user_id="U125",
                message="Positive feedback",
            ),
        ]

        for event in events:
            repository.create_reaction_event(event)

        # Fetch negative reactions grouped by source_adapter_message_id
        result = repository.fetch_reaction_event_by_bot_id(bot_id, Reaction.NEGATIVE)

        assert len(result) == 1  # Only 1 conversation with negative reactions
        assert result[0]["source_adapter_message_id"] == "conv1"
        assert result[0]["reactions_count"] == 2  # Two negative reactions in conv1

    def test_fetch_total_conversation(self, setup_repository):
        repository = setup_repository
        bot_id = uuid4()

        # Add test data
        events = [
            ReactionEventCreate(
                bot_id=bot_id,
                reaction=Reaction.NEGATIVE,
                source_adapter=MessageAdapter.SLACK,
                source_adapter_message_id="conv1",
                source_adapter_user_id="U123",
                message="Negative feedback",
            ),
            ReactionEventCreate(
                bot_id=bot_id,
                reaction=Reaction.POSITIVE,
                source_adapter=MessageAdapter.SLACK,
                source_adapter_message_id="conv2",
                source_adapter_user_id="U124",
                message="Positive feedback",
            ),
            ReactionEventCreate(
                bot_id=bot_id,
                reaction=Reaction.NEGATIVE,
                source_adapter=MessageAdapter.SLACK,
                source_adapter_message_id="conv2",
                source_adapter_user_id="U125",
                message="Another negative feedback in same conversation",
            ),
        ]

        for event in events:
            repository.create_reaction_event(event)

        # Fetch total unique conversations
        total_conversations = repository.fetch_total_conversation(bot_id)

        assert total_conversations == 2
