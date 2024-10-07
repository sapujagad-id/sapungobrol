import pytest
from chat.exceptions import ChatResponseGenerationError
from .anthropic_chat import ChatAnthropic


@pytest.fixture
def sample_query():
    return "Who is Jokowi?"


@pytest.fixture
def sample_context():
    return "Jokowi is the president of Indonesia."


@pytest.fixture
def chat():
    return ChatAnthropic()


class TestChatAnthropic:

    def test_generate_response_with_context(self, mocker, chat, sample_query, sample_context):

        mock_create = mocker.patch.object(chat, "generate_response")
        mock_create.return_value = "Mocked response content"
        
        response = chat.generate_response(query=sample_query, context=sample_context)
        
        assert response == "Mocked response content"
        mock_create.assert_called_once()

    def test_generate_response_without_context(self, mocker, chat, sample_query):

        mock_create = mocker.patch.object(chat, "generate_response")
        mock_create.return_value = "Mocked response content"

        response = chat.generate_response(query=sample_query)
        
        assert response == "Mocked response content"
        mock_create.assert_called_once()

    def test_generate_response_with_empty_query(self, mocker, chat):

        mock_create = mocker.patch.object(chat, "generate_response")
        mock_create.return_value = ""
        response = chat.generate_response(query="")

        assert response == ""
        mocker.patch.object(chat, "generate_response").assert_not_called()
