import pytest
from .anthropic_chat import ChatAnthropic
from unittest.mock import patch, MagicMock
from chat.exceptions import ChatResponseGenerationError


@pytest.fixture
def sample_query():
    return "Who is Jokowi?"


@pytest.fixture
def sample_context():
    return "Jokowi is the president of Indonesia."


@pytest.fixture
def chat():
    return ChatAnthropic(api_key="random-str")


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
    
    @patch("anthropic.resources.Messages.create")
    def test_api_call_mock(self, mock_create, chat, sample_query):
        mock_create.return_value = MagicMock(content=[MagicMock(text="Mocked response content")])
        
        chat.generate_response(sample_query)
        
        mock_create.assert_called_once()
        _, kwargs = mock_create.call_args
        assert kwargs["model"] == "claude-3-haiku-20240307"
        assert kwargs["max_tokens"] == 1024
        
    @patch("anthropic.resources.Messages.create")
    def test_generate_response_failure(self, mock_create, chat):
        mock_create.side_effect = Exception("API error")

        with pytest.raises(ChatResponseGenerationError) as excinfo:
            chat.generate_response("Test query")

        assert str(excinfo.value) == "Error generating response: API error"
