from abc import abstractmethod, ABC
from uuid import uuid4, UUID
from loguru import logger

from datetime import datetime
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy import Column, Enum, Uuid, String, Text, DateTime

from bot.helper import relative_time

from .bot import BotUpdate, MessageAdapter, ModelEngine, BotResponse, BotCreate

Base = declarative_base()


class BotModel(Base):
    """
    A chatbot instance.
    """

    __tablename__ = "bots"

    id = Column(Uuid, primary_key=True)
    name = Column(String(255), nullable=False)
    system_prompt = Column(Text(length=2048), nullable=False)
    model = Column(Enum(ModelEngine, validate_strings=True), nullable=False)
    adapter = Column(Enum(MessageAdapter, validate_strings=True), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    slug = Column(String(255), unique=True)

    def __repr__(self):
        return f"Bot id:{self.id}"


class BotRepository(ABC):
    @abstractmethod
    def find_bots(self, skip: int, limit: int) -> list[BotResponse]:
        pass

    @abstractmethod
    def find_bot_by_id(self, bot_id: str) -> BotModel:
        pass

    @abstractmethod
    def create_bot(self, bot_create: BotCreate):
        pass

    @abstractmethod
    def update_bot(self, bot, bot_update: BotUpdate):
        pass
    
    @abstractmethod
    def delete_bot(self, bot):
        pass

    @abstractmethod
    def find_bot_by_slug(self, slug):
        pass


class PostgresBotRepository(BotRepository):
    def __init__(self, session: sessionmaker) -> None:
        self.create_session = session
        self.logger = logger.bind(service="PostgresBotRepository")

    def find_bots(self, skip: int, limit: int) -> list[BotResponse]:
        with self.create_session() as session:
            bots = session.query(BotModel).offset(skip).limit(limit).all()
            for bot in bots:
                bot.updated_at_relative = relative_time(bot.updated_at)
            return bots
        
    def find_bot_by_slug(self, slug):
        with self.create_session() as session:
            with self.logger.catch(
                message=f"Bot with slug:{slug} not found", reraise=True
            ):
                return session.query(BotModel).filter(BotModel.slug == slug).first()

    def find_bot_by_id(self, bot_id):
        with self.create_session() as session:
            with self.logger.catch(
                message=f"Bot with ID:{bot_id} not found", reraise=True
            ):
                return session.query(BotModel).filter(BotModel.id == bot_id).first()

    def create_bot(self, bot_create: BotCreate):
        with self.create_session() as session:
            with self.logger.catch(message="create bot error", reraise=True):
                bot_id = uuid4()
                new_bot = BotModel(**bot_create.model_dump(), id=bot_id)
                session.add(new_bot)
                session.commit()

    def update_bot(self, bot, bot_update: BotUpdate = None):
        with self.create_session() as session:
            with self.logger.catch(message="update bot error", reraise=True):
                session.add(bot)

                for field, value in vars(bot_update).items():
                    if hasattr(bot, field):
                        setattr(bot, field, value)

                bot.updated_at = datetime.now()

                session.commit()
                return bot
    
    def delete_bot(self, bot):
        pass
