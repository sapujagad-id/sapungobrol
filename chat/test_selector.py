from unittest.mock import MagicMock, patch

import pytest

from bot import ModelEngine

from . import ChatEngineSelector
from .anthropic_chat import ChatAnthropic
from .openai_chat import ChatOpenAI


class TestChatEngineSelector:
    @pytest.fixture(scope="session")
    def sample_string(self) -> str:
        return "Random-str"
    @pytest.fixture(scope="session")
    def sample_int(self) -> int:
        return 1

    @patch("chat.PostgresHandler")
    def test_select_openai_engine(self, mock_postgres_handler, sample_string, sample_int):
        mock_postgres_handler_instance = MagicMock()
        mock_postgres_handler.return_value = mock_postgres_handler_instance

        engine_selector = ChatEngineSelector(
            openai_api_key=sample_string,
            anthropic_api_key=sample_string,
            postgres_db=sample_string,
            postgres_user=sample_string,
            postgres_password=sample_string,
            postgres_host=sample_string,
            postgres_port=sample_int
        )
        
        mock_retriever_instance = MagicMock()
        engine_selector.retriever = mock_retriever_instance

        engine = engine_selector.select_engine(ModelEngine.OPENAI)

        assert isinstance(engine, ChatOpenAI)
    
    @patch("chat.PostgresHandler")
    def test_select_anthropic_engine(self, mock_postgres_handler, sample_string, sample_int):
        mock_postgres_handler_instance = MagicMock()
        mock_postgres_handler.return_value = mock_postgres_handler_instance

        engine_selector = ChatEngineSelector(
            openai_api_key=sample_string,
            anthropic_api_key=sample_string,
            postgres_db=sample_string,
            postgres_user=sample_string,
            postgres_password=sample_string,
            postgres_host=sample_string,
            postgres_port=sample_int
        )
        
        mock_retriever_instance = MagicMock()
        engine_selector.retriever = mock_retriever_instance

        engine = engine_selector.select_engine(ModelEngine.ANTHROPIC)

        assert isinstance(engine, ChatAnthropic)