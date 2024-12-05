from abc import ABC, abstractmethod
from datetime import datetime
from uuid import uuid4

from loguru import logger
from sqlalchemy import Column, DateTime, Enum, String, Text, Uuid
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from common.shared_types import MessageAdapter

from .reaction_event import Reaction, ReactionEventCreate

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
    def delete_reaction_event(self, reaction: Reaction, source_adapter_message_id: str, source_adapter_user_id: str): # pragma: no cover
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
    
    def delete_reaction_event(
        self,
        reaction: Reaction,
        source_adapter_message_id: str,
        source_adapter_user_id: str
    ):
        self.logger.bind(
            reaction=reaction,
            message_id=source_adapter_message_id,
            user_id=source_adapter_user_id,
        ).info("deleting reaction event")

        with self.create_session() as session:
            with self.logger.catch(message="delete reaction event error", reraise=True):
                reaction_event = (
                    session.query(ReactionEventModel)
                    .filter_by(
                        reaction=reaction,
                        source_adapter_message_id=source_adapter_message_id,
                        source_adapter_user_id=source_adapter_user_id,
                    )
                    .first()
                )
                
                if reaction_event:
                    session.delete(reaction_event)
                    session.commit()
                    self.logger.info("Reaction event deleted successfully")
                else:
                    self.logger.warning("No matching reaction event found for deletion")
