import pytest


from bot import ModelEngine
from . import ChatEngineSelector
from .openai_chat import ChatOpenAI
from .anthropic_chat import ChatAnthropic


class TestChatEngineSelector:
    @pytest.fixture(scope="session")
    def api_key(self) -> str:
        return "Random-str"

    def test_select_openai_engine(self, api_key):
        engine_selector = ChatEngineSelector(openai_api_key=api_key, anthropic_api_key=api_key)
        engine = engine_selector.select_engine(ModelEngine.OPENAI)

        assert isinstance(engine, ChatOpenAI)
    
    def test_select_anthropic_engine(self, api_key):
        engine_selector = ChatEngineSelector(openai_api_key=api_key, anthropic_api_key=api_key)
        engine = engine_selector.select_engine(ModelEngine.ANTHROPIC)

        assert isinstance(engine, ChatAnthropic)
