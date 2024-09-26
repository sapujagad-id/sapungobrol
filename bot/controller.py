from abc import ABC, abstractmethod
from fastapi import HTTPException

from .bot import BotCreate, BotNotFound, BotUpdate, NameIsRequired, SystemPromptIsRequired, UnsupportedAdapter, UnsupportedModel
from .service import BotService


class BotController(ABC):
    @abstractmethod
    def fetch_chatbots(self):
        pass

    @abstractmethod
    def create_chatbot(self, request: BotCreate):
        pass

    @abstractmethod
    def update_chatbot(self, request: BotUpdate):
        pass


class BotControllerV1(BotController):
    def __init__(self, service: BotService) -> None:
        super().__init__()
        self.service = service

    def fetch_chatbots(self, skip = 0, limit:int = 10):
        return self.service.get_chatbots(skip, limit)

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
        except UnsupportedAdapter:
            raise HTTPException(status_code=400, detail="Unsupported message adapter")
        except Exception:
            raise HTTPException(status_code=500, detail="Something went wrong")
        
    def update_chatbot(self, bot_id, request: BotUpdate):
        try:
            self.service.update_chatbot(bot_id, request)
            return {"detail": "Bot updated successfully!"}
        except NameIsRequired:
            raise HTTPException(status_code=400, detail="Name is required")
        except SystemPromptIsRequired:
            raise HTTPException(status_code=400, detail="System prompt is required")
        except UnsupportedModel:
            raise HTTPException(status_code=400, detail="Unsupported model")
        except UnsupportedAdapter:
            raise HTTPException(status_code=400, detail="Unsupported message adapter")
        except BotNotFound:
            raise HTTPException(status_code=400, detail="Bot not found")
        except Exception:
            raise HTTPException(status_code=500, detail="Something went wrong")
