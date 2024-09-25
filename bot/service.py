from abc import abstractmethod, ABC
from loguru import logger

from .repository import BotRepository
from .bot import Bot, BotCreate


class BotService(ABC):
    @abstractmethod
    def get_chatbots(self, skip: int, limit: int) -> list[Bot]:
        pass

    @abstractmethod
    def create_chatbot(self, request: BotCreate):
        pass


class BotServiceV1(BotService):
    def __init__(self, repository: BotRepository) -> None:
        super().__init__()
        self.repository = repository
        self.logger = logger.bind(service="BotService")

    def get_chatbots(self, skip: int, limit: int) -> list[Bot]:
        return self.repository.find_bots(skip, limit)

    def create_chatbot(self, request: BotCreate):
        request.validate()

        self.repository.create_bot(request)

        return
