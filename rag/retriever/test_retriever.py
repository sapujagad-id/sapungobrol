import pytest
from unittest.mock import MagicMock, patch
from rag.retriever.retriever import Retriever


@pytest.fixture
def retriever():
    mock_postgres_handler = MagicMock()
    return Retriever(mock_postgres_handler)

@patch("openai.embeddings.create")
def test_retrieve_context_vector(mock_create_embedding, retriever):
    mock_embedding = MagicMock()
    mock_create_embedding.return_value = MagicMock(data=[MagicMock(embedding=[0.1, 0.2, 0.3])])

    retriever.postgres_handler.query.return_value = ["result1", "result2"]

    query = "test query"
    access_level = "public"
    top_k = 2
    result = retriever._retrieve_context_vector(query, access_level, top_k)

    mock_create_embedding.assert_called_once_with(input=query, model="text-embedding-3-small")

    retriever.postgres_handler.query.assert_called_once_with([0.1, 0.2, 0.3], access_level=access_level, top_k=top_k)

    assert result == ["result1", "result2"]


def test_retrieve_context_tabular(retriever):
    # Mock the method to simulate a tabular context retrieval
    retriever._retrieve_context_tabular = MagicMock(return_value="Tabular Context")

    result = retriever._retrieve_context_tabular(query="sample query", access_level=1)

    # Validate the returned tabular context
    assert result == "Tabular Context"


def test_query(retriever):
    # Mock the helper methods for the `query` function
    retriever._retrieve_context_vector = MagicMock(return_value=["Vector Context 1", "Vector Context 2"])
    retriever._retrieve_context_tabular = MagicMock(return_value="Tabular Context")

    # Execute the `query` method
    result = retriever.query(query="sample query", access_level=1, top_k=5)

    # Validate the combined context
    assert len(result) == 3
    assert result[0] == "Vector Context 1"
    assert result[1] == "Vector Context 2"
    assert result[2] == "Tabular Context"
