from abc import abstractmethod, ABC
from datetime import datetime
from loguru import logger
from sqlalchemy import Column, Uuid, Enum, String, Text, DateTime, func
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from uuid import uuid4

from common.shared_types import MessageAdapter
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
    def create_reaction_event(self, event_create: ReactionEventCreate): # pragma: no cover
        pass

    @abstractmethod
    def fetch_reaction_event_by_bot_id(self, bot_id: str, reaction: Reaction):
        pass

    @abstractmethod
    def fetch_total_conversation(self, bot_id:str):
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

    def fetch_reaction_event_by_bot_id(self, bot_id: str, reaction: Reaction) -> list[ReactionEventModel]:
        with self.create_session() as session:
            result = (
                session.query(
                    ReactionEventModel.source_adapter_message_id,
                    func.count(ReactionEventModel.id).label("reactions_count"),
                )
                .filter(
                    ReactionEventModel.bot_id == bot_id,
                    ReactionEventModel.reaction == reaction,
                )
                .group_by(ReactionEventModel.source_adapter_message_id)
                .all()
            )
            return [
                {
                    "source_adapter_message_id": row.source_adapter_message_id,
                    "reactions_count": row.reactions_count,
                }
                for row in result
            ]

    def fetch_total_conversation(self, bot_id:str):
        with self.create_session() as session:
            with self.logger.catch(message="fetching reaction events error", reraise=True):
                total_conversations = (
                    session.query(ReactionEventModel.source_adapter_message_id)
                    .filter(ReactionEventModel.bot_id == bot_id)
                    .distinct()
                    .count()
                )
                return total_conversations