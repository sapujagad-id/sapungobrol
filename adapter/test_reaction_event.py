import pytest

from .reaction_event import ReactionEventCreate, Reaction, UnknownReaction
from bot.bot import MessageAdapter
from uuid import uuid4


class TestReactionEvent:
    def mock_slack_reaction_added_event(self, reaction: str):
        event = {
            "type": "reaction_added",
            "user": "U1234567890",
            "reaction": reaction,
            "item": {
                "type": "message",
                "channel": "C1234567890",
                "ts": "1731075911.249209",
            },
            "item_user": "U9876543210",
            "event_ts": "1731076540.000900",
        }
        return event

    @pytest.fixture
    def mock_slack_negative_reaction_event(self):
        return self.mock_slack_reaction_added_event("-1")

    @pytest.fixture
    def mock_slack_positive_reaction_event(self):
        return self.mock_slack_reaction_added_event("+1")

    def test_reaction_event_create(
        self,
        mock_slack_negative_reaction_event,
        mock_slack_positive_reaction_event,
    ):
        bot_id = uuid4()
        message = "Hi there!"

        slack_reaction_events = [
            (mock_slack_negative_reaction_event, Reaction.NEGATIVE),
            (mock_slack_positive_reaction_event, Reaction.POSITIVE),
        ]

        for event, expected_reaction in slack_reaction_events:
            reaction_event_create = ReactionEventCreate.from_slack_reaction(
                str(bot_id),
                message,
                event,
            )

            assert reaction_event_create.bot_id == bot_id
            assert reaction_event_create.reaction == expected_reaction
            assert reaction_event_create.source_adapter == MessageAdapter.SLACK
            assert (
                reaction_event_create.source_adapter_message_id == event["item"]["ts"]
            )
            assert reaction_event_create.source_adapter_user_id == event["user"]
            assert reaction_event_create.message == message

    def test_reaction_event_create_unknown_reaction(self):
        bot_id = "U1234567890"
        message = "Hi there!"

        slack_reaction_event = self.mock_slack_reaction_added_event("unknown_reaction")

        with pytest.raises(UnknownReaction):
            ReactionEventCreate.from_slack_reaction(
                bot_id,
                message,
                slack_reaction_event,
            )
