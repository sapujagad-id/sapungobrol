from abc import abstractmethod, ABC
from uuid import uuid4, UUID
from loguru import logger

from datetime import datetime
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy import Column, Enum, Uuid, String, Text, DateTime, func, ForeignKey, case

from bot.helper import relative_time

from adapter.reaction_event_repository import ReactionEventModel
from .bot import BotUpdate, MessageAdapter, ModelEngine, BotResponse, BotCreate


Base = declarative_base()

class ThreadModel(Base):
    __tablename__ = "threads"

    id = Column(Uuid, primary_key=True)
    bot_id = Column(Uuid, ForeignKey("bots.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

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
    def find_bots(self, skip: int, limit: int) -> list[BotResponse]: # pragma: no cover
        pass

    @abstractmethod
    def find_bot_by_id(self, bot_id: str) -> BotModel: # pragma: no cover
        pass

    @abstractmethod
    def create_bot(self, bot_create: BotCreate): # pragma: no cover
        pass

    @abstractmethod
    def update_bot(self, bot, bot_update: BotUpdate): # pragma: no cover
        pass
    
    @abstractmethod
    def delete_bot(self, bot): # pragma: no cover
        pass

    @abstractmethod
    def find_bot_by_slug(self, slug): # pragma: no cover
        pass
    
    @abstractmethod
    def get_dashboard_data(self, bot_id: UUID): # pragma: no cover
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
        with self.create_session() as session:
            with self.logger.catch(message="delete bot error", reraise=True):
                session.delete(bot)

                session.commit()
                
    def get_dashboard_data(self, bot_id: UUID):
        with self.create_session() as session:
            try:
                # Fetch the last 5 threads with counts of positive and negative reactions
                last_threads_subquery = (
                    session.query(
                        ReactionEventModel.message,
                        ReactionEventModel.reaction,
                        ReactionEventModel.created_at,
                        func.row_number()
                        .over(
                            partition_by=ReactionEventModel.message,
                            order_by=ReactionEventModel.created_at.desc()
                        )
                        .label("row_num"),
                    )
                    .filter(ReactionEventModel.bot_id == bot_id)
                    .subquery()
                )

                last_threads = (
                    session.query(
                        last_threads_subquery.c.message,
                        func.count(
                            case(
                                (last_threads_subquery.c.reaction == "NEGATIVE", 1),
                                else_=None
                            )
                        ).label("negative_count"),
                        func.count(
                            case(
                                (last_threads_subquery.c.reaction == "POSITIVE", 1),
                                else_=None
                            )
                        ).label("positive_count"),
                    )
                    .filter(last_threads_subquery.c.row_num == 1)  # Only the latest row for each message
                    .group_by(last_threads_subquery.c.message)
                    .limit(5)
                    .all()
                )

                # Total cumulative threads for the bot
                cumulative_threads = (
                    session.query(func.count(ThreadModel.id))
                    .filter(ThreadModel.bot_id == bot_id)
                    .scalar()
                )

                return {
                    "last_threads": [
                        {
                            "thread": t[0],
                            "negative_count": t[1],
                            "positive_count": t[2],
                        }
                        for t in last_threads
                    ],
                    "cumulative_threads": cumulative_threads or 0,  # Ensure it's valid
                }
            except Exception as e:
                self.logger.error(
                    f"Error in get_dashboard_data for bot_id: {bot_id}. Error: {str(e)}"
                )
                raise

