from abc import abstractmethod, ABC

from datetime import datetime
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import Column, Enum, Uuid, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base

from .bot import ModelEngine, Bot

Base = declarative_base()


class BotModel(Base):
    """
    A chatbot instance.
    """

    __tablename__ = "bots"

    id = Column(Uuid, primary_key=True)
    name = Column(String(255), nullable=False)
    system_prompt = Column(Text(length=2048), nullable=False)
    model = Column(Enum(ModelEngine), nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def __repr__(self):
        return f"Bot id:{self.id}"


class BotRepository(ABC):
    @abstractmethod
    def find_bots(self) -> list[Bot]:
        pass


class PostgresBotRepository(BotRepository):
    def __init__(self, session: sessionmaker[Session]) -> None:
        self.create_session = session

    def find_bots(self) -> list[Bot]:
        with self.create_session() as session:
            return session.query(BotModel).all()
