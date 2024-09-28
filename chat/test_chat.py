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
def mock_openai(mocker):
    mock_openai_instance = mocker.patch('openai.OpenAI')
    mock_openai_instance.return_value.run = MagicMock(return_value="Apache Doris is a real-time analytics SQL data warehouse.")
    return mock_openai_instance

class TestChat:
    
    def __init__(self):
        self.chat = ChatOpenAI()

    def test_generate_response_with_context(self, sample_query, sample_context, mock_openai):
        response = self.chat.generate_response(sample_query, sample_context)

        assert response is not None
        assert isinstance(response, str)
        assert "Apache Doris" in response  
        assert "real-time analytics" in response  

    def test_generate_response_no_context(self, sample_query, mock_openai):

        response = self.chat.generate_response(sample_query, None)

        assert response is not None
        assert isinstance(response, str)
        assert "Apache Doris" in response 

    def test_generate_empty_response(self, mock_openai):

        response = self.chat.generate_response("", "")
        assert response == ""