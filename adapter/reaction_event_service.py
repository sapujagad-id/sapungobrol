from abc import abstractmethod, ABC
from fastapi import HTTPException
from loguru import logger

from adapter.reaction_event import Reaction, ReactionNotFound, UnknownReaction

from .reaction_event_repository import ReactionEventRepository


class ReactionEventService(ABC):
    @abstractmethod
    def get_reaction_event_by_bot_id(self, bot_id: int, reaction: Reaction):
        pass


class ReactionEventServiceV1(ReactionEventService):
    def __init__(self, repository: ReactionEventRepository) -> None:
        super().__init__()
        self.repository = repository
        self.logger = logger.bind(service="ReactionEventService")

    def get_reaction_event_by_bot_id(self, bot_id: str, reaction: Reaction = Reaction.NEGATIVE):
        """
        Fetch reaction events by bot_id and reaction type and return some metrics for analysis.

        Args:
            bot_id (UUID): The ID of the chatbot.
            reaction (Reaction): The type of reaction to filter by (e.g., POSITIVE, NEGATIVE).

        Returns:
            "total_conversations",
            "average_negative/positive_reactions_per_conversation",
            "recent_conversations",
            "top_negative/positive_conversations",
        """
        try:
            conversation_data = self.repository.fetch_reaction_event_by_bot_id(bot_id, reaction)

            if not conversation_data:
                raise ReactionNotFound

            total_conversations = self.repository.fetch_total_conversation(bot_id)
            total_reactions = sum(
                item["reactions_count"] for item in conversation_data
            )
            average_reactions_per_conversation = (
                total_reactions / total_conversations if total_conversations > 0 else 0
            )

            recent_conversations = sorted(
                conversation_data, key=lambda x: x["source_adapter_message_id"], reverse=True
            )[:5]
            top_reaction_conversations = sorted(
                conversation_data, key=lambda x: x["reactions_count"], reverse=True
            )[:5]

            return {
                "total_conversations": total_conversations,
                f"average_{reaction.lower()}_reactions_per_conversation": average_reactions_per_conversation,
                "recent_conversations": recent_conversations,
                f"top_{reaction.lower()}_conversations": top_reaction_conversations,
            }
        except ReactionNotFound:
            raise HTTPException(404, ReactionNotFound.message)
        except Exception as e:
            self.logger.error(f"Unexpected error fetching reaction events for bot {bot_id}: {str(e)}")
            raise HTTPException(500, str(e))