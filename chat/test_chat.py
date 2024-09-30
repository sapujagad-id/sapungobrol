import pytest
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
def chat():
    """Fixture to initialize the ChatOpenAI instance."""
    return ChatOpenAI()

class TestChat:

    def test_generate_response_with_context(self, chat, sample_query, sample_context):
        response = chat.generate_response(sample_query, sample_context)

        assert response is not None
        assert isinstance(response, str)
        assert "Apache Doris" in response  
        assert "real-time analytics" in response  

    def test_generate_response_no_context(self, chat, sample_query):
        response = chat.generate_response(sample_query, None)

        assert response is not None
        assert isinstance(response, str)
        assert "Apache Doris" in response 

    def test_generate_empty_response(self, chat):
        response = chat.generate_response("", "")
        
        assert response == ""
        
    def test_refine_query_before_chat(self, chat, sample_query, sample_context):
        # simulating query refinement
        refined_query = sample_query + " for real-time analytics in SQL data warehouse?"
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
        assert any(phrase in response.lower() for phrase in [
            "not enough information", 
            "not mentioned", 
            "does not contain", 
            "irrelevant context",
            "cannot answer"
        ])
    
    def test_chat_remember_history(self, chat, sample_history, sample_query_history):
        response = chat.generate_response(sample_history, None)
        response = chat.generate_response(sample_query_history, None)
        
        assert response is not None
        assert isinstance(response, str)
        assert "Molvative Squarepants" in response