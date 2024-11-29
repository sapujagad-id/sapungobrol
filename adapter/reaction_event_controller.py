from abc import ABC, abstractmethod
from fastapi import HTTPException

from adapter.reaction_event_service import ReactionEventService



class ReactionEventController(ABC):
    @abstractmethod
    def get_reaction_event_by_chatbot_id(self, bot_id:str):
        pass


class ReactionEventControllerV1(ReactionEventController):
    GENERAL_ERROR_MESSAGE = "Something went wrong"
    
    def __init__(self, service: ReactionEventService) -> None:
        super().__init__()
        self.service = service

    def get_reaction_event_by_chatbot_id(self, bot_id:str):
        return self.service.get_reaction_event_by_bot_id(bot_id)
