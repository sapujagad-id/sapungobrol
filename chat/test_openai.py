import pytest
from unittest.mock import MagicMock, patch
from .openai_chat import ChatOpenAI
from chat.exceptions import ChatResponseGenerationError
from chat import ChatEngineSelector
from bot import ModelEngine

from rag.retriever.retriever import Retriever


@pytest.fixture
def retriever():
    mock_postgres_handler = MagicMock()
    return Retriever(mock_postgres_handler)


@pytest.fixture
def sample_query():
    return "what is apache doris"


@pytest.fixture
def sample_access_level():
    return 1


@pytest.fixture
def sample_history():
    return "My name is Molvative Squarepants. Remember my name!"


@pytest.fixture
def sample_query_history():
    return "Say my name!"


@pytest.fixture
def sample_query_forget_history():
    return "Do you know my name? Yes or No"


@pytest.fixture
def chat(retriever):
    return ChatOpenAI(retriever)


@pytest.fixture
def mock_openai_response():
    class MockMessage:
        def __init__(self, content):
            self.content = content

    class MockChoice:
        def __init__(self, message):
            self.message = message

    class MockResponse:
        def __init__(self):
            self.choices = [MockChoice(MockMessage("Mocked response content"))]

    return MockResponse()


class TestChat:

    @patch("openai.chat.completions.create")
    def test_generate_response_with_access_level(
        self, mock_create, chat, sample_query, sample_access_level, mock_openai_response
    ):
        mock_create.return_value = mock_openai_response
        response = chat.generate_response(sample_query, sample_access_level)

        assert response == "Mocked response content"
        mock_create.assert_called_once()
        _, kwargs = mock_create.call_args
        assert kwargs["model"] == "gpt-4o-mini"
        assert len(kwargs["messages"]) == 3
        assert "Given a query:" in kwargs["messages"][1]["content"]

    @patch("openai.chat.completions.create")
    def test_generate_response_no_access_level(
        self, mock_create, chat, sample_query, sample_access_level, mock_openai_response
    ):
        mock_create.return_value = mock_openai_response
        response = chat.generate_response(sample_query, sample_access_level)

        assert response == "Mocked response content"
        mock_create.assert_called_once()
        _, kwargs = mock_create.call_args
        assert kwargs["model"] == "gpt-4o-mini"
        assert len(kwargs["messages"]) == 3

    def test_generate_empty_response(self, chat):
        response = chat.generate_response("", "")
        assert response == ""

    @patch("openai.chat.completions.create")
    def test_chat_remember_history(
        self,
        mock_create,
        chat,
        sample_history,
        sample_query_history,
        sample_access_level,
        mock_openai_response,
    ):
        mock_create.return_value = mock_openai_response
        chat.generate_response(sample_history, sample_access_level)
        chat.generate_response(sample_query_history, sample_access_level)

        assert len(chat.history) == 5  # Including system message and responses
        assert sample_history in chat.history[1]["content"]
        assert sample_query_history in chat.history[3]["content"]

    @patch("openai.chat.completions.create")
    def test_chat_reset_history(
        self,
        mock_create,
        chat,
        sample_history,
        sample_query_forget_history,
        mock_openai_response,
    ):
        mock_create.return_value = mock_openai_response
        chat.generate_response(sample_history, None)
        chat.reset_history()
        chat.generate_response(sample_query_forget_history, None)

        assert (
            len(chat.history) == 3
        )  # Should only contain system message and the last user query

    @patch("openai.chat.completions.create")
    def test_refine_query_before_chat(
        self, mock_create, chat, sample_query, sample_access_level, mock_openai_response
    ):
        mock_create.return_value = mock_openai_response
        refined_query = sample_query + " for real-time analytics in SQL data warehouse?"
        response = chat.generate_response(refined_query, sample_access_level)

        assert response == "Mocked response content"
        mock_create.assert_called_once()
        _, kwargs = mock_create.call_args
        assert "real-time analytics" in kwargs["messages"][1]["content"]
        assert "SQL data warehouse" in kwargs["messages"][1]["content"]

    @patch("openai.chat.completions.create")
    def test_generate_response_failure(self, mock_create, chat):
        mock_create.side_effect = Exception("API error")

        with pytest.raises(ChatResponseGenerationError) as excinfo:
            chat.generate_response("Test query")

        assert str(excinfo.value) == "Error generating response: API error"
