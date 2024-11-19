import openai as op

from bot import ModelEngine

from .openai_chat import ChatOpenAI
from .engine import ChatEngine
from .anthropic_chat import ChatAnthropic

from rag.retriever.retriever import Retriever
from rag.vectordb.postgres_handler import PostgresHandler

class ChatEngineSelector:
    def __init__(
        self,
        openai_api_key: str,
        anthropic_api_key: str,
        postgres_db: str,
        postgres_user: str,
        postgres_password: str,
        postgres_host: str,
        postgres_port: int
    ) -> None:
        op.api_key = openai_api_key
        self.anthropic_api_key = anthropic_api_key
        
        self.retriever = Retriever(
            PostgresHandler(
                db_name=postgres_db,
                user=postgres_user,
                password=postgres_password,
                host=postgres_host,
                port=postgres_port,
                dimension=1536
            )
        )

    def select_engine(self, engine_type: ModelEngine) -> ChatEngine:
        if engine_type == ModelEngine.OPENAI:
            return ChatOpenAI(self.retriever)
        elif engine_type == ModelEngine.ANTHROPIC:
            return ChatAnthropic(self.retriever, api_key=self.anthropic_api_key)
