import pytest
from unittest.mock import MagicMock
from .chat import ChatOpenAI

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
def mock_openai(mocker):
    mock_openai_instance = mocker.patch('openai.OpenAI')
    mock_openai_instance.return_value.run = MagicMock(return_value="Apache Doris is a real-time analytics SQL data warehouse.")
    return mock_openai_instance

@pytest.fixture
def chat():
    """Fixture to initialize the ChatOpenAI instance."""
    return ChatOpenAI()

class TestChat:

    def test_generate_response_with_context(self, chat, sample_query, sample_context, mock_openai):
        response = chat.generate_response(sample_query, sample_context)

        assert response is not None
        assert isinstance(response, str)
        assert "Apache Doris" in response  
        assert "real-time analytics" in response  

    def test_generate_response_no_context(self, chat, sample_query, mock_openai):
        response = chat.generate_response(sample_query, None)

        assert response is not None
        assert isinstance(response, str)
        assert "Apache Doris" in response 

    def test_generate_empty_response(self, chat, mock_openai):
        response = chat.generate_response("", "")
        
        assert response == ""
        
    def test_refine_query_before_chat(self, chat, sample_query, sample_context):
        original_query = sample_query
        
        # simulating query refinement
        refined_query = "what is apache doris for real-time analytics in SQL data warehouse?"
        response = chat.generate_response(refined_query, sample_context)

        assert response is not None
        assert isinstance(response, str)
        assert "Apache Doris" in response
        assert "real-time analytics" in response
        assert "SQL data warehouse" in response
        
    def test_no_hallucination_without_context(self, chat, sample_query, irrelevant_context):
        response = chat.generate_response(sample_query, irrelevant_context)

        assert response is not None
        assert isinstance(response, str)
        assert "not enough information" in response
    
    def test_chat_remember_history(self, chat, sample_history, sample_query_history):
        response = chat.generate_response(sample_history, None)
        response = chat.generate_response(sample_query_history, None)
        
        assert response is not None
        assert isinstance(response, str)
        assert "Molvative Squarepants" in response