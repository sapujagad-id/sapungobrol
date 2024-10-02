import pytest
from unittest.mock import patch, MagicMock
from .chat import ChatOpenAI
from config import AppConfig

@pytest.fixture
def mock_app_config():
    mock_config = MagicMock(spec=AppConfig)
    mock_config.openai_api_key = "mock-api-key"
    return mock_config

@pytest.fixture
def sample_query():
    return "what is apache doris"

@pytest.fixture
def sample_context():
    return "Apache Doris is a modern MPP-based SQL data warehouse for real-time analytics."

@pytest.fixture
def irrelevant_context():
    return "This context is not relevant to the query."

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
def chat(mock_app_config):
    """Fixture to initialize the ChatOpenAI instance with a mocked AppConfig."""
    with patch('chat.chat.AppConfig', return_value=mock_app_config):
        return ChatOpenAI()

@pytest.fixture
def mock_openai_response():
    return {
        'choices': [
            {
                'message': {
                    'content': 'Mocked response content'
                }
            }
        ]
    }

class TestChat:

    @patch('openai.ChatCompletion.create')
    def test_generate_response_with_context(self, mock_create, chat, sample_query, sample_context, mock_openai_response):
        mock_create.return_value = mock_openai_response
        response = chat.generate_response(sample_query, sample_context)

        assert response == 'Mocked response content'
        mock_create.assert_called_once()
        _, kwargs = mock_create.call_args
        assert kwargs['model'] == "gpt-4o-mini"
        assert len(kwargs['messages']) == 2
        assert "Given a context:" in kwargs['messages'][0]['content']
        assert "Given a query:" in kwargs['messages'][0]['content']

    @patch('openai.ChatCompletion.create')
    def test_generate_response_no_context(self, mock_create, chat, sample_query, mock_openai_response):
        mock_create.return_value = mock_openai_response
        response = chat.generate_response(sample_query, None)

        assert response == 'Mocked response content'
        mock_create.assert_called_once()
        _, kwargs = mock_create.call_args
        assert kwargs['model'] == "gpt-4o-mini"
        assert len(kwargs['messages']) == 2
        assert kwargs['messages'][0]['content'] == sample_query

    def test_generate_empty_response(self, chat):
        response = chat.generate_response("", "")
        assert response == ""

    @patch('openai.ChatCompletion.create')
    def test_chat_remember_history(self, mock_create, chat, sample_history, sample_query_history, mock_openai_response):
        mock_create.return_value = mock_openai_response
        chat.generate_response(sample_history, None)
        chat.generate_response(sample_query_history, None)
        
        assert len(chat.history) == 4
        assert chat.history[0]['content'] == sample_history
        assert chat.history[2]['content'] == sample_query_history

    @patch('openai.ChatCompletion.create')
    def test_chat_reset_history(self, mock_create, chat, sample_history, sample_query_forget_history, mock_openai_response):
        mock_create.return_value = mock_openai_response
        chat.generate_response(sample_history, None)
        chat.reset_history()
        chat.generate_response(sample_query_forget_history, None)
        
        assert len(chat.history) == 2

    @patch('openai.ChatCompletion.create')
    def test_refine_query_before_chat(self, mock_create, chat, sample_query, sample_context, mock_openai_response):
        mock_create.return_value = mock_openai_response
        refined_query = sample_query + " for real-time analytics in SQL data warehouse?"
        response = chat.generate_response(refined_query, sample_context)

        assert response == 'Mocked response content'
        mock_create.assert_called_once()
        _, kwargs = mock_create.call_args
        assert "real-time analytics" in kwargs['messages'][0]['content']
        assert "SQL data warehouse" in kwargs['messages'][0]['content']

    @patch('openai.ChatCompletion.create')
    def test_no_hallucination_without_context(self, mock_create, chat, sample_query, irrelevant_context, mock_openai_response):
        mock_create.return_value = mock_openai_response
        response = chat.generate_response(sample_query, irrelevant_context)

        assert response == 'Mocked response content'
        mock_create.assert_called_once()
        _, kwargs = mock_create.call_args
        assert irrelevant_context in kwargs['messages'][0]['content']