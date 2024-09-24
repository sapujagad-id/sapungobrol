from abc import ABC, abstractmethod
from fastapi import HTTPException

from .bot import BotCreate, NameIsRequired, SystemPromptIsRequired, UnsupportedModel
from .service import BotService


class BotController(ABC):
    @abstractmethod
    def fetch_chatbots(self):
        pass

    @abstractmethod
    def create_chatbot(self, request: BotCreate):
        pass


class BotControllerV1(BotController):
    def __init__(self, service: BotService) -> None:
        super().__init__()
        self.service = service

    def fetch_chatbots(self):
        return self.service.get_chatbots()

    def create_chatbot(self, request: BotCreate):
        try:
            self.service.create_chatbot(request)
            return {"detail": "Bot created successfully!"}
        except NameIsRequired:
            raise HTTPException(status_code=400, detail="Name is required")
        except SystemPromptIsRequired:
            raise HTTPException(status_code=400, detail="System prompt is required")
        except UnsupportedModel:
            raise HTTPException(status_code=400, detail="Unsupported model")
        except Exception:
            raise HTTPException(status_code=500, detail="Something went wrong")
