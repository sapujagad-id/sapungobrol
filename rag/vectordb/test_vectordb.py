import pytest
from unittest.mock import MagicMock, patch
from rag.vectordb.node_storage import PineconeNodeStorage
from rag.vectordb.pinecone_handler import PineconeHandler
import openai
from pinecone.core.openapi.shared.exceptions import UnauthorizedException


@pytest.fixture
def mock_pinecone_handler():
    """Mock PineconeHandler for testing."""
    mock_handler = MagicMock(spec=PineconeHandler)
    return mock_handler

@pytest.fixture
def mock_openai_embed(mocker):
    """Mock the OpenAI embedding API."""
    mock_embed = mocker.patch('openai.embeddings.create')
    mock_embed.return_value = MagicMock(
        data=[MagicMock(embedding=[0.1, 0.2, 0.3])]  # Sample embedding vector
    )
    return mock_embed

def test_pinecone_node_storage_happy_path(mock_pinecone_handler, mock_openai_embed):
    """Test storing nodes in Pinecone with proper embeddings."""
    storage = PineconeNodeStorage(pinecone_handler=mock_pinecone_handler)
    nodes = ["This is a test node", "Another test node"]
    
    storage.store_nodes(nodes)

    # Verify that OpenAI embedding is called twice (for two nodes)
    assert mock_openai_embed.call_count == 2
    mock_openai_embed.assert_any_call(input="This is a test node", model="text-embedding-3-small")
    mock_openai_embed.assert_any_call(input="Another test node", model="text-embedding-3-small")
    
    # Verify that vectors were upserted into Pinecone
    mock_pinecone_handler.upsert_vectors.assert_called_once()
    upserted_vectors = mock_pinecone_handler.upsert_vectors.call_args[0][0]
    assert len(upserted_vectors) == 2  # We are storing 2 vectors
    assert upserted_vectors[0]['values'] == [0.1, 0.2, 0.3]
    assert upserted_vectors[1]['values'] == [0.1, 0.2, 0.3]

def test_pinecone_node_storage_empty_nodes(mock_pinecone_handler, mock_openai_embed):
    """Test storing no nodes."""
    storage = PineconeNodeStorage(pinecone_handler=mock_pinecone_handler)
    nodes = []

    with pytest.raises(ValueError) as excinfo:
        storage.store_nodes(nodes)
    
    assert str(excinfo.value) == "No vectors to store."
        
    # Ensure no OpenAI embedding calls and no vectors are upserted
    mock_openai_embed.assert_not_called()
    mock_pinecone_handler.upsert_vectors.assert_not_called()
            


def test_pinecone_node_storage_openai_failure(mock_pinecone_handler, mocker):
    """Test OpenAI embedding failure."""
    storage = PineconeNodeStorage(pinecone_handler=mock_pinecone_handler)
    nodes = ["This will fail"]

    with pytest.raises(Exception, match="OpenAI error"):
        storage.store_nodes(nodes)

    # Ensure no vectors are upserted since embedding failed
    mock_pinecone_handler.upsert_vectors.assert_not_called()


# PineconeHandler tests

@pytest.fixture
def mock_pinecone(mocker):
    """Mock the Pinecone API."""
    mock_pc = mocker.patch('rag.vectordb.pinecone_handler.Pinecone')
    mock_pc_instance = mock_pc.return_value
    mock_pc_instance.list_indexes.return_value = [{'name': 'broom'}]
    return mock_pc_instance

def test_pinecone_handler_existing_index(mock_pinecone):
    """Test PineconeHandler with an existing index."""
    handler = PineconeHandler(api_key="fake_api_key", index_name="broom", dimension=1536)

    # Check that it does not attempt to create a new index
    mock_pinecone.create_index.assert_not_called()
    mock_pinecone.list_indexes.assert_called_once()
    assert handler.index is not None

def test_pinecone_handler_upsert_vectors(mock_pinecone):
    """Test upserting vectors to Pinecone."""
    handler = PineconeHandler(api_key="fake_api_key", index_name="broom", dimension=1536)
    vectors = [{"id": "1", "values": [0.1, 0.2, 0.3]}]

    handler.upsert_vectors(vectors)

    # Check that upsert_vectors was called on the Pinecone index
    handler.index.upsert.assert_called_once_with(vectors)

def test_pinecone_handler_create_index_failure(mock_pinecone):
    """Test failure when Pinecone API fails to create an index."""
    mock_pinecone.list_indexes.return_value = [{'name': 'different_index'}]
    mock_pinecone.create_index.side_effect = Exception("Pinecone error")

    with pytest.raises(Exception, match="Pinecone error"):
        PineconeHandler(api_key="fake_api_key", index_name="new_index", dimension=1536)

def test_pinecone_handler_query(mock_pinecone):
    """Test querying vectors from Pinecone."""
    handler = PineconeHandler(api_key="fake_api_key", index_name="broom", dimension=1536)
    query_vector = [0.1, 0.2, 0.3]
    top_k = 5

    handler.query(query_vector, top_k)

    # Check that query was called on the Pinecone index with correct parameters
    handler.index.query.assert_called_once_with(vector=query_vector, top_k=top_k)


def test_pinecone_handler_initialization_error():
    """Test PineconeHandler initialization with invalid parameters."""
    with pytest.raises(UnauthorizedException, match="Invalid API Key"):
        PineconeHandler(api_key="fake_api_key", index_name="test", dimension=-1)