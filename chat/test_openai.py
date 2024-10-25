import pytest
from unittest.mock import patch
from .openai_chat import ChatOpenAI
from chat.exceptions import ChatResponseGenerationError
from chat import ChatEngineSelector
from bot import ModelEngine


@pytest.fixture
def sample_query():
    return "what is apache doris"


@pytest.fixture
def sample_context():
    return (
        "Apache Doris is a modern MPP-based SQL data warehouse for real-time analytics."
    )


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
def sample_insufficient_context_query():
    return "What is the capital of France?"


@pytest.fixture
def chat():
    selector = ChatEngineSelector(openai_api_key="testkey", anthropic_api_key="testkey")
    return selector.select_engine(ModelEngine.OPENAI)


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


@pytest.fixture
def mock_openai_response_insufficient():
    class MockMessage:
        def __init__(self, content):
            self.content = content

    class MockChoice:
        def __init__(self, message):
            self.message = message

    class MockResponse:
        def __init__(self):
            self.choices = [MockChoice(MockMessage("I don't know"))]

    return MockResponse()


class TestChat:

    @patch("openai.chat.completions.create")
    def test_generate_response_with_context(
        self, mock_create, chat, sample_query, sample_context, mock_openai_response
    ):
        mock_create.return_value = mock_openai_response
        response = chat.generate_response(sample_query, sample_context)

        assert response == "Mocked response content"
        mock_create.assert_called_once()
        _, kwargs = mock_create.call_args
        assert kwargs["model"] == "gpt-4o-mini"
        assert len(kwargs["messages"]) == 3
        assert "Given a context:" in kwargs["messages"][1]["content"]
        assert "Given a query:" in kwargs["messages"][1]["content"]

    @patch("openai.chat.completions.create")
    def test_generate_response_no_context(
        self, mock_create, chat, sample_query, mock_openai_response
    ):
        mock_create.return_value = mock_openai_response
        response = chat.generate_response(sample_query, None)

        assert response == "Mocked response content"
        mock_create.assert_called_once()
        _, kwargs = mock_create.call_args
        assert kwargs["model"] == "gpt-4o-mini"
        assert len(kwargs["messages"]) == 3
        assert kwargs["messages"][1]["content"] == sample_query

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
        mock_openai_response,
    ):
        mock_create.return_value = mock_openai_response
        chat.generate_response(sample_history, None)
        chat.generate_response(sample_query_history, None)

        assert len(chat.history) == 5  # Including system message and responses
        assert chat.history[1]["content"] == sample_history
        assert chat.history[3]["content"] == sample_query_history

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
        self, mock_create, chat, sample_query, sample_context, mock_openai_response
    ):
        mock_create.return_value = mock_openai_response
        refined_query = sample_query + " for real-time analytics in SQL data warehouse?"
        response = chat.generate_response(refined_query, sample_context)

        assert response == "Mocked response content"
        mock_create.assert_called_once()
        _, kwargs = mock_create.call_args
        assert "real-time analytics" in kwargs["messages"][1]["content"]
        assert "SQL data warehouse" in kwargs["messages"][1]["content"]

    @patch("openai.chat.completions.create")
    def test_no_hallucination_without_context(
        self, mock_create, chat, sample_query, irrelevant_context, mock_openai_response
    ):
        mock_create.return_value = mock_openai_response
        response = chat.generate_response(sample_query, irrelevant_context)

        assert response == "Mocked response content"
        mock_create.assert_called_once()
        _, kwargs = mock_create.call_args
        assert irrelevant_context in kwargs["messages"][1]["content"]

    @patch("openai.chat.completions.create")
    def test_generate_response_failure(self, mock_create, chat):
        mock_create.side_effect = Exception("API error")

        with pytest.raises(ChatResponseGenerationError) as excinfo:
            chat.generate_response("Test query")

        assert str(excinfo.value) == "Error generating response: API error"

    @patch("openai.chat.completions.create")
    def test_insufficient_context(
        self,
        mock_create,
        chat,
        sample_insufficient_context_query,
        mock_openai_response_insufficient,
    ):
        mock_create.return_value = mock_openai_response_insufficient
        # Use an irrelevant context or no context
        irrelevant_context = "This context does not contain relevant information."
        response = chat.generate_response(
            sample_insufficient_context_query, irrelevant_context
        )

        assert response == "I don't know"  # Expecting "I don't know"
        mock_create.assert_called_once()
        _, kwargs = mock_create.call_args
        assert irrelevant_context in kwargs["messages"][1]["content"]
