import openai as op

from bot import ModelEngine

from .openai_chat import ChatOpenAI
from .engine import ChatEngine
from .anthropic_chat import ChatAnthropic

class ChatEngineSelector:
    def __init__(self, openai_api_key: str) -> None:
        op.api_key = openai_api_key

    def select_engine(self, engine_type: ModelEngine) -> ChatEngine:
        if engine_type == ModelEngine.OPENAI:
            return ChatOpenAI()
