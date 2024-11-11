from abc import abstractmethod, ABC
from datetime import datetime
from loguru import logger
from sqlalchemy import Column, Uuid, Enum, String, Text, DateTime
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from uuid import uuid4

from bot.bot import MessageAdapter
from .reaction_event import ReactionEventCreate, Reaction

Base = declarative_base()


class ReactionEventModel(Base):
    __tablename__ = "reaction_events"

    id = Column(Uuid, primary_key=True)
    bot_id = Column(Uuid, nullable=False)
    reaction = Column(Enum(Reaction, validate_strings=True), nullable=False)
    source_adapter = Column(Enum(MessageAdapter, validate_strings=True), nullable=False)
    source_adapter_message_id = Column(String(255), nullable=False)
    source_adapter_user_id = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now)


class ReactionEventRepository(ABC):
    @abstractmethod
    def create_reaction_event(self, event_create: ReactionEventCreate):
        pass


class PostgresReactionEventRepository(ReactionEventRepository):
    def __init__(self, session: sessionmaker[Session]) -> None:
        self.create_session = session
        self.logger = logger.bind(service="PostgresReactionEventRepository")

    def create_reaction_event(self, event_create: ReactionEventCreate):
        self.logger.bind(
            bot=event_create.bot_id,
            reaction=event_create.reaction,
            message_id=event_create.source_adapter_message_id,
            adapter=event_create.source_adapter,
        ).info("saving reaction event")

        with self.create_session() as session:
            with self.logger.catch(message="saving reaction event error", reraise=True):
                reaction_event_id = uuid4()
                new_reaction_event = ReactionEventModel(
                    **event_create.model_dump(), id=reaction_event_id
                )
                session.add(new_reaction_event)
                session.commit()
