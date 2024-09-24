from abc import abstractmethod, ABC
from loguru import logger

from .repository import BotRepository
from .bot import Bot


class BotService(ABC):
    @abstractmethod
    def get_chatbots(self) -> list[Bot]:
        pass


class BotServiceV1(BotService):
    def __init__(self, repository: BotRepository) -> None:
        super().__init__()
        self.repository = repository
        self.logger = logger.bind(service="BotService")

    def get_chatbots(self) -> list[Bot]:
        self.logger.info("fetching chatbots")
        return self.repository.find_bots()
