from abc import abstractmethod, ABC
from loguru import logger

from .repository import BotRepository
from .bot import BotResponse, BotCreate, BotUpdate


class BotService(ABC):
    @abstractmethod
    def get_chatbots(self, skip: int, limit: int) -> list[BotResponse]:
        pass

    @abstractmethod
    def create_chatbot(self, request: BotCreate):
        pass

    @abstractmethod
    def update_chatbot(self, bot_id: str, request: BotUpdate):
        pass

    @abstractmethod
    def get_chatbot_by_id(self, bot_id: str):
        pass


class BotServiceV1(BotService):
    def __init__(self, repository: BotRepository) -> None:
        super().__init__()
        self.repository = repository
        self.logger = logger.bind(service="BotService")

    def get_chatbots(self, skip: int, limit: int) -> list[BotResponse]:
        return self.repository.find_bots(skip, limit)

    def create_chatbot(self, request: BotCreate):
        request.validate()

        self.repository.create_bot(request)

    def update_chatbot(self, bot_id, request: BotUpdate):

        bot = self.repository.find_bot_by_id(bot_id)
        request.validate(bot)

        self.repository.update_bot(bot, request)

    def get_chatbot_by_id(self, bot_id):
        pass