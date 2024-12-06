import enum
from typing import Any

from pydantic import UUID4, BaseModel, ConfigDict

from common.shared_types import MessageAdapter


class UnknownReaction(Exception):
    message = "Unknown reaction found"


class Reaction(enum.StrEnum):
    POSITIVE = "Positive"
    NEGATIVE = "Negative"


class ReactionEventCreate(BaseModel):
    bot_id: UUID4
    reaction: Reaction
    source_adapter: MessageAdapter
    source_adapter_message_id: str
    source_adapter_user_id: str
    message: str

    model_config = ConfigDict(from_attributes=True)

    @staticmethod
    def from_slack_reaction(bot_id: str, message: str, event: dict[str, Any]):
        if event["reaction"] == "-1":
            reaction = Reaction.NEGATIVE
        elif event["reaction"] == "+1":
            reaction = Reaction.POSITIVE
        else:
            raise UnknownReaction

        return ReactionEventCreate(
            bot_id=bot_id,
            reaction=reaction,
            source_adapter=MessageAdapter.SLACK,
            source_adapter_message_id=event["item"]["ts"],
            source_adapter_user_id=event["user"],
            message=message,
        )
