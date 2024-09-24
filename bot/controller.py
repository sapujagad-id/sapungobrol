from abc import ABC, abstractmethod

from .service import BotService


class BotController(ABC):
    @abstractmethod
    def fetch_chatbots(self):
        pass


class BotControllerV1(BotController):
    def __init__(self, service: BotService) -> None:
        super().__init__()
        self.service = service

    def fetch_chatbots(self):
        return self.service.get_chatbots()
