import pytest
from unittest.mock import patch, MagicMock
from chat.exceptions import ChatResponseGenerationError
from .anthropic_chat import ChatAnthropic


@pytest.fixture
def retriever():
    mock_retriever = MagicMock()
    mock_retriever.query.return_value = ["Mocked context"]
    return mock_retriever


@pytest.fixture
def sample_query():
    return "Who is Jokowi?"


@pytest.fixture
def sample_access_level():
    return 1


@patch("chat.anthropic_chat.Anthropic")  # Ensure this matches where Anthropic is imported in your codebase
class TestChatAnthropic:
    def test_generate_response_with_access_level(self, mock_anthropic, retriever, sample_query, sample_access_level):
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="Mocked response content")]
        )

        chat = ChatAnthropic(retriever, api_key="random-str")
        response = chat.generate_response(query=sample_query, access_level=sample_access_level)

        assert response == "Mocked response content"
        mock_client.messages.create.assert_called_once()

    def test_generate_response_without_access_level(self, mock_anthropic, retriever, sample_query):
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="Mocked response content")]
        )

        chat = ChatAnthropic(retriever, api_key="random-str")
        response = chat.generate_response(query=sample_query)

        assert response == "Mocked response content"
        mock_client.messages.create.assert_called_once()

    def test_generate_response_with_empty_query(self, mock_anthropic, retriever):
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client

        chat = ChatAnthropic(retriever, api_key="random-str")
        response = chat.generate_response(query="")

        assert response == ""
        mock_client.messages.create.assert_not_called()

    def test_api_call_mock(self, mock_anthropic, retriever, sample_query):
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(
            content=[MagicMock(text="Mocked response content")]
        )

        chat = ChatAnthropic(retriever, api_key="random-str")
        chat.generate_response(sample_query)

        mock_client.messages.create.assert_called_once()

    def test_generate_response_failure(self, mock_anthropic, retriever):
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("API error")

        chat = ChatAnthropic(retriever, api_key="random-str")
        with pytest.raises(ChatResponseGenerationError) as excinfo:
            chat.generate_response("Test query")

        assert str(excinfo.value) == "Error generating response: API error"
