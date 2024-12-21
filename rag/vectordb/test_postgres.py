import os
from unittest.mock import MagicMock, call, create_autospec, patch

import pytest

from rag.vectordb.postgres_handler import PostgresHandler
from rag.vectordb.postgres_node_storage import PostgresNodeStorage


@pytest.fixture
def mock_postgres_handler():
    """Mock PostgresHandler for testing."""
    handler = create_autospec(PostgresHandler)
    return handler

@pytest.fixture
def mock_openai_embed(mocker):
    """Mock the OpenAI embedding API."""
    mock_embed = mocker.patch('openai.embeddings.create')
    mock_embed.return_value = MagicMock(
        data=[MagicMock(embedding=[0.1, 0.2, 0.3])]  # Sample embedding vector
    )
    return mock_embed

@pytest.fixture
def mock_psycopg2_connect(mocker):
    """Mock psycopg2 connect function."""
    mock_conn = mocker.patch("psycopg2.connect", autospec=True)
    mock_cursor = mock_conn.return_value.cursor.return_value
    return mock_conn, mock_cursor

@pytest.fixture(autouse=True)
def mock_total_access_levels_env_var(monkeypatch):
    """Mock the TOTAL_ACCESS_LEVELS environment variable to always be 5 for tests."""
    monkeypatch.setenv("TOTAL_ACCESS_LEVELS", "5")
    
@pytest.fixture(autouse=True)
def mock_postgres_password_env_var(monkeypatch):
    """Mock the POSTGRES_PASSWORD environment variable."""
    monkeypatch.setenv("POSTGRES_PASSWORD", "random123")


def test_postgres_node_storage_happy_path(mock_postgres_handler, mock_openai_embed):
    """Test storing nodes in Postgres with proper embeddings."""
    storage = PostgresNodeStorage(postgres_handler=mock_postgres_handler)
    nodes = ["This is a test node", "Another test node"]
    
    storage.store_nodes(nodes, access_level=2)

    # Verify that OpenAI embedding is called twice (for two nodes)
    assert mock_openai_embed.call_count == 2
    mock_openai_embed.assert_any_call(input="This is a test node", model="text-embedding-3-small")
    mock_openai_embed.assert_any_call(input="Another test node", model="text-embedding-3-small")
    
    # Verify that vectors were upserted into Postgres
    mock_postgres_handler.upsert_vectors.assert_called_once()
    upserted_vectors = mock_postgres_handler.upsert_vectors.call_args[0][0]
    assert len(upserted_vectors) == 2  # We are storing 2 vectors
    assert upserted_vectors[0]['values'] == [0.1, 0.2, 0.3]
    assert upserted_vectors[1]['values'] == [0.1, 0.2, 0.3]

def test_postgres_node_storage_empty_nodes(mock_postgres_handler, mock_openai_embed):
    """Test storing no nodes."""
    storage = PostgresNodeStorage(postgres_handler=mock_postgres_handler)
    nodes = []

    with pytest.raises(ValueError) as excinfo:
        storage.store_nodes(nodes, access_level=2)
    
    assert str(excinfo.value) == "No vectors to store."
        
    # Ensure no OpenAI embedding calls and no vectors are upserted
    mock_openai_embed.assert_not_called()
    mock_postgres_handler.upsert_vectors.assert_not_called()

def test_postgres_node_storage_openai_failure(mock_postgres_handler, mocker):
    """Test OpenAI embedding failure."""
    mocker.patch('openai.embeddings.create', side_effect=Exception("OpenAI error"))

    storage = PostgresNodeStorage(postgres_handler=mock_postgres_handler)
    nodes = ["This will fail"]

    with pytest.raises(Exception, match="OpenAI error"):
        storage.store_nodes(nodes, access_level=2)

    # Ensure no vectors are upserted since embedding failed
    mock_postgres_handler.upsert_vectors.assert_not_called()


def test_postgres_handler_query(mock_psycopg2_connect):
    """Test querying vectors from Postgres."""
    _, mock_cursor = mock_psycopg2_connect
    mock_password = os.getenv("POSTGRES_TEST_PASSWORD")
    handler = PostgresHandler(db_name="test_db", user="user", password=mock_password, host="localhost", port=5432, dimension=1536)
    
    query_vector = [0.1, 0.2, 0.3]
    top_k = 5
    access_level = 3

    # Simulate some returned rows
    mock_cursor.fetchall.return_value = [("id1", 0.01), ("id2", 0.02)]
    results = handler.query(query_vector, access_level=access_level, top_k=top_k)

    # Verify query was executed with the correct SQL for the access level table
    expected_query = """
            SELECT item_id, text_content, embedding <-> %s::vector AS distance
            FROM index_l3
            ORDER BY distance
            LIMIT %s;
        """
    actual_query = mock_cursor.execute.call_args[0][0].strip()
    assert actual_query == expected_query.strip()
    assert mock_cursor.execute.call_args[0][1] == (query_vector, top_k)
    assert results == [("id1", 0.01), ("id2", 0.02)]
    handler.close()

def test_postgres_handler_initialization_error(mocker):
    """Test initialization error handling for PostgresHandler."""
    mocker.patch("psycopg2.connect", side_effect=Exception("Database connection error"))
    mock_password = os.getenv("POSTGRES_TEST_PASSWORD")

    with pytest.raises(Exception, match="Database connection error"):
        PostgresHandler(db_name="test_db", user="user", password=mock_password, host="localhost", port=5432, dimension=1536)
        
def test_upsert_vectors(mock_psycopg2_connect):
    """Test the upsert_vectors method to ensure correct insertion of vectors."""
    _, mock_cursor = mock_psycopg2_connect

    with patch.dict(os.environ, {"TOTAL_ACCESS_LEVELS": "5"}):
        handler = PostgresHandler(
            db_name="test_db",
            user="user",
            password="password",
            host="localhost",
            port=5432,
            dimension=1536
        )

    vectors = [
        {"id": "item1", "values": [0.1, 0.2, 0.3]},
        {"id": "item2", "values": [0.4, 0.5, 0.6]}
    ]
    level = 2

    handler.upsert_vectors(vectors, level=level)

    insert_calls = [
        call(
            f"INSERT INTO index_l{lvl} (item_id, embedding, text_content) VALUES (%s, %s, %s) "
            f"ON CONFLICT (item_id) DO UPDATE SET embedding = EXCLUDED.embedding, text_content = EXCLUDED.text_content;",
            (vector["id"], vector["values"], '')
        )
        for lvl in range(level, handler.total_access_levels + 1)
        for vector in vectors
    ]

    mock_cursor.execute.assert_has_calls(insert_calls, any_order=False)

    handler.close()