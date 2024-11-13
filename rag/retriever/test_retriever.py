import pytest
from unittest.mock import MagicMock
from rag.retriever.retriever import Retriever


@pytest.fixture
def retriever():
    return Retriever()


def test_retrieve_context_vector(retriever):
    # Mock the method to simulate a vector retrieval
    retriever._retrieve_context_vector = MagicMock(return_value=["Vector Context 1", "Vector Context 2"])

    result = retriever._retrieve_context_vector(query="sample query", access_level=1, top_k=5)

    # Validate the returned vector context
    assert len(result) == 2
    assert result[0] == "Vector Context 1"
    assert result[1] == "Vector Context 2"


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
