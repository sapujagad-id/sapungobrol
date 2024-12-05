from typing import List
from unittest.mock import MagicMock, patch

import pytest

from bot import ModelEngine
from chat import ChatEngineSelector
from chat.exceptions import ChatResponseGenerationError
from rag.retriever.retriever import Retriever


@pytest.fixture
def retriever(): # pragma: no cover
    mock_postgres_handler = MagicMock()
    return Retriever(mock_postgres_handler)


@pytest.fixture
def sample_query(): # pragma: no cover
    return "what is apache doris"


@pytest.fixture
def sample_access_level(): # pragma: no cover
    return 1


@pytest.fixture
def sample_history(): # pragma: no cover
    return "My name is Molvative Squarepants. Remember my name!"


@pytest.fixture
def sample_query_history(): # pragma: no cover
    return "Say my name!"


@pytest.fixture
def sample_query_forget_history(): # pragma: no cover
    return "Do you know my name? Yes or No"

@pytest.fixture(autouse=True)
def mock_total_access_levels_env_var(monkeypatch):
    monkeypatch.setenv("TOTAL_ACCESS_LEVELS", "5")
    monkeypatch.setenv("OPENAI_API_KEY", "testkey")


class MockCompletionChoice: # pragma: no cover
    def __init__(self, content: str):
        self.message = MagicMock(content=content)

class MockEmbeddingResponse: # pragma: no cover
    class DataItem:
        def __init__(self, embedding):
            self.embedding = embedding # pragma: no cover

    def __init__(self):
        self.data = [self.DataItem([0.1, 0.2, 0.3])] # pragma: no cover
        
class MockCompletion:
    def __init__(self, choices: List[MockCompletionChoice]):
        self.choices = choices
        self.id = "mock_id"
        self.created = 123456789
        self.model = "mock_model"
        self.object = "text_completion"

@pytest.fixture
def mock_openai_api():
    with patch("openai.chat.completions.create") as mock_chat_completion, \
         patch("openai.embeddings.create") as mock_embeddings:

        # Mock embeddings response
        mock_embeddings.return_value = MagicMock(
            data=[MagicMock(embedding=[0.1, 0.2, 0.3])]
        )

        # Mock chat completions response
        mock_chat_completion.return_value = MockCompletion(
            choices=[MockCompletionChoice(content="Mocked response content")]
        )

        yield mock_chat_completion
        
@pytest.fixture
def chat(mock_openai_api):
    with patch("psycopg2.connect") as mock_connect, \
         patch("rag.vectordb.postgres_handler.PostgresHandler") as MockPostgresHandler, \
         patch("rag.retriever.retriever.Retriever") as MockRetriever:
        
        # Mock psycopg2.connect to prevent actual DB connections
        mock_connect.return_value = MagicMock()
        MockPostgresHandler.return_value = MagicMock()
        MockRetriever.return_value = MagicMock()

        # Instantiate ChatEngineSelector with mocked dependencies
        selector = ChatEngineSelector(
            openai_api_key="testkey",
            anthropic_api_key="testkey",
            postgres_db="mock_db",
            postgres_user="mock_user",
            postgres_password="mock_password",
            postgres_host="mock_host",
            postgres_port=5432,
        )
        yield selector.select_engine(ModelEngine.OPENAI)


class TestChat:

    def test_generate_response_with_access_level(self, chat, mock_openai_api):
        query = "what is apache doris"
        access_level = 1

        response = chat.generate_response(query, access_level)
        assert response == "Mocked response content"

    def test_generate_response_no_access_level(self, chat):
        query = "what is apache doris"
        response = chat.generate_response(query, None)
        assert response == "Mocked response content"

    def test_generate_empty_response(self, chat):
        response = chat.generate_response("", "")
        assert response == ""

    def test_chat_remember_history(self, chat):
        history = "My name is Molvative Squarepants. Remember my name!"
        query = "Say my name!"
        access_level = 1

        chat.generate_response(history, access_level)
        chat.generate_response(query, access_level)

        assert len(chat.history) == 5
        assert history in chat.history[1]["content"]
        assert query in chat.history[3]["content"]

    def test_chat_reset_history(self, chat):
        history = "My name is Molvative Squarepants. Remember my name!"
        query = "Do you know my name? Yes or No"

        chat.generate_response(history, None)
        chat.reset_history()
        chat.generate_response(query, None)

        assert len(chat.history) == 3

    def test_refine_query_before_chat(self, chat):
        query = "what is apache doris for real-time analytics in SQL data warehouse?"
        access_level = 1

        response = chat.generate_response(query, access_level)
        assert response == "Mocked response content"

    def test_generate_response_failure(self, chat):
        with patch("openai.chat.completions.create", side_effect=Exception("API error")):
            with pytest.raises(ChatResponseGenerationError) as excinfo:
                chat.generate_response("Test query")

            assert str(excinfo.value) == "Error generating response: API error"