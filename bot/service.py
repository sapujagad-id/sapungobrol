from abc import ABC, abstractmethod
from uuid import UUID

from loguru import logger

from .bot import BotCreate, BotNotFound, BotResponse, BotUpdate, SlugIsExist
from .repository import BotRepository


class BotService(ABC):
    @abstractmethod
    def get_chatbots(self, skip: int, limit: int) -> list[BotResponse]: # pragma: no cover
        pass

    @abstractmethod
    def create_chatbot(self, request: BotCreate): # pragma: no cover
        pass

    @abstractmethod
    def update_chatbot(self, bot_id: str, request: BotUpdate): # pragma: no cover
        pass
    
    @abstractmethod
    def delete_chatbot(self, bot_id: str): # pragma: no cover
        pass

    @abstractmethod
    def get_chatbot_by_id(self, bot_id: str): # pragma: no cover
        pass

    @abstractmethod
    def get_chatbot_by_slug(self, slug: str): # pragma: no cover
        pass

    @abstractmethod
    def is_slug_exist(self, slug: str): # pragma: no cover
        pass
    
    @abstractmethod
    def get_dashboard_data(self, bot_id: UUID): # pragma: no cover
        pass


class BotServiceV1(BotService):
    def __init__(self, repository: BotRepository) -> None:
        super().__init__()
        self.repository = repository
        self.logger = logger.bind(service="BotService")

    def is_slug_exist(self, slug: str) -> bool:
        # Use the repository to check if the slug exists
        try:
            bot = self.repository.find_bot_by_slug(slug)
            return bot is not None
        except Exception as e:
            self.logger.error(f"Error checking if slug exists: {e}")
            return False

    def get_chatbots(self, skip: int, limit: int) -> list[BotResponse]:
        return self.repository.find_bots(skip, limit)

    def create_chatbot(self, request: BotCreate):
        request.validate()
        if self.repository.find_bot_by_slug(request.slug):
            raise SlugIsExist
        self.repository.create_bot(request)

    def update_chatbot(self, bot_id, request: BotUpdate):
        bot = self.repository.find_bot_by_id(bot_id)
        request.validate(bot)
        if bot.slug != request.slug and self.repository.find_bot_by_slug(request.slug):
            raise SlugIsExist 
        self.repository.update_bot(bot, request)
    
    def delete_chatbot(self, bot_id: str):
        bot = self.repository.find_bot_by_id(bot_id)
        
        if not bot:
            raise BotNotFound

        self.repository.delete_bot(bot)

    def get_chatbot_by_id(self, bot_id):
        bot = self.repository.find_bot_by_id(bot_id)
        return bot if bot else None
    
    def get_chatbot_by_slug(self, slug):
        bot = self.repository.find_bot_by_slug(slug)
        return bot if bot else None
    
    def get_dashboard_data(self, bot_id: UUID):
        return self.repository.get_dashboard_data(bot_id)
