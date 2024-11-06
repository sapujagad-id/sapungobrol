from unittest.mock import MagicMock, create_autospec, patch

import pytest
from sqlalchemy import Connection, Engine

from rag.sql.postgres_db_loader import (get_postgres_engine, load_csv_to_db,
                                        load_xlsx_to_db)


@pytest.fixture
def mock_engine():
    mock = create_autospec(Engine)
    # Patch the engine's connect method to return a mocked connection
    with patch('rag.sql.postgres_query_engine.get_postgres_engine', return_value=mock):
        yield mock

@pytest.fixture
def mock_connection(mock_engine):
    mock_conn = MagicMock(spec=Connection)
    mock_engine.connect.return_value.__enter__.return_value = mock_conn
    yield mock_conn

@pytest.fixture
def mock_sql_database():
    with patch('rag.sql.postgres_query_engine.SQLDatabase') as mock:
        instance = mock.return_value
        instance.get_table_info.return_value = "table_info"
        yield instance

@pytest.fixture
def mock_openai():
    mock_message = MagicMock()
    mock_message.content = "Mocked response"
    
    mock_chat = MagicMock()
    mock_chat.message = mock_message
    
    mock = MagicMock()
    mock.chat.return_value = mock_chat
    
    with patch('rag.sql.postgres_query_engine.OpenAI', return_value=mock):
        yield mock

@pytest.fixture
def mock_nl_sql_engine():
    mock = MagicMock()
    mock_response = MagicMock()
    mock_response.metadata = {'sql_query': 'SELECT * FROM test_table WHERE condition = true'}
    mock.return_value.query.return_value = mock_response
    
    with patch('rag.sql.postgres_query_engine.NLSQLTableQueryEngine', mock):
        yield mock

@pytest.fixture
def mock_get_table_schema():
    with patch('rag.sql.postgres_query_engine.get_table_schema', 
              return_value=['column1 TEXT', 'column2 INT']):
        yield

@pytest.fixture
def mock_extract_signature():
    with patch('rag.sql.postgres_query_engine.extract_signature',
              return_value=('', 'test_signature')):
        yield

@pytest.fixture
def mock_check_sql_security():
    with patch('rag.sql.postgres_query_engine.check_sql_security',
              return_value=(True, "OK")):
        yield

def test_setup_llm():
    """Test LLM setup."""
    from rag.sql.postgres_query_engine import setup_llm
    
    with patch('rag.sql.postgres_query_engine.OpenAI') as mock_openai:
        mock_instance = MagicMock()
        mock_openai.return_value = mock_instance
        
        result = setup_llm()
        assert result == mock_instance
        mock_openai.assert_called_once_with(model="gpt-4o-mini")

def test_setup_query_engine(mock_engine, mock_sql_database, mock_nl_sql_engine, 
                          mock_get_table_schema):
    """Test query engine setup."""
    from rag.sql.postgres_query_engine import setup_query_engine
    
    _, schema = setup_query_engine("test_table")
    
    assert schema == ['column1 TEXT', 'column2 INT']
    mock_sql_database.get_table_info.assert_not_called()

def test_run_query(mock_connection, mock_sql_database, mock_openai, mock_nl_sql_engine,
                  mock_get_table_schema, mock_check_sql_security, mock_extract_signature):
    """Test running a query with mock data returned."""
    from rag.sql.postgres_query_engine import run_query
    
    mock_result = MagicMock()
    mock_result.fetchall.return_value = [('result1',), ('result2',)]
    mock_connection.execute.return_value = mock_result
    
    result = run_query("test query", user_access_level=3, table_name="test_table")
    
    assert result == "Mocked response"
    mock_connection.execute.assert_called_once()
    mock_nl_sql_engine.return_value.query.assert_called_once()

def test_run_query_no_results(mock_connection, mock_sql_database, mock_openai, 
                            mock_nl_sql_engine, mock_get_table_schema, 
                            mock_check_sql_security, mock_extract_signature):
    """Test running a query with no results."""
    from rag.sql.postgres_query_engine import run_query
    
    mock_result = MagicMock()
    mock_result.fetchall.return_value = []
    mock_connection.execute.return_value = mock_result
    
    result = run_query("test query", user_access_level=3, table_name="test_table")
    
    assert result == "I'm sorry, but there is no data available for your access level or the specified query."

def test_run_query_security_check_fails(mock_engine, mock_sql_database, mock_nl_sql_engine,
                                      mock_get_table_schema, mock_extract_signature):
    """Test running a query that fails the security check."""
    from rag.sql.postgres_query_engine import run_query

    with patch('rag.sql.postgres_query_engine.check_sql_security',
              return_value=(False, "Security violation")):
        
        with pytest.raises(ValueError, match="Security check failed: Security violation"):
            run_query(
                "test query",
                user_access_level=3,
                table_name="test_table"
            )

@patch("rag.sql.postgres_db_loader.create_engine")
def test_get_postgres_engine(mock_create_engine):
    """Test the creation of a PostgreSQL engine."""
    # Mock environment variables for database configuration
    with patch.dict("os.environ", {
        "POSTGRES_DB": "test_db",
        "POSTGRES_USER": "test_user",
        "POSTGRES_PASSWORD": "test_password",
        "POSTGRES_HOST": "test_host",
        "POSTGRES_PORT": "5432"
    }):
        engine = get_postgres_engine()
        
        mock_create_engine.assert_called_once_with(
            "postgresql://test_user:test_password@test_host:5432/test_db"
        )
        assert engine == mock_create_engine.return_value

@patch("rag.sql.postgres_db_loader.get_postgres_engine")
@patch("rag.sql.postgres_db_loader.CSVProcessor")
def test_load_csv_to_db(mock_csv_processor, mock_get_engine):
    """Test loading CSV data into PostgreSQL."""
    mock_engine = mock_get_engine.return_value
    mock_df = MagicMock()
    mock_csv_processor.return_value._load_document.return_value = mock_df

    engine = load_csv_to_db("dummy_path.csv", access_level=3, table_name="test_table")

    mock_csv_processor.return_value._load_document.assert_called_once()
    mock_df.__setitem__.assert_called_once_with("access_level", 3)  # Ensure "access_level" is set
    mock_df.to_sql.assert_called_once_with("test_table", con=mock_engine, if_exists="replace", index=False)
    assert engine == mock_engine

@patch("rag.sql.postgres_db_loader.get_postgres_engine")
@patch("rag.sql.postgres_db_loader.XLSXProcessor")
def test_load_xlsx_to_db(mock_xlsx_processor, mock_get_engine):
    """Test loading XLSX data into PostgreSQL."""
    mock_engine = mock_get_engine.return_value
    mock_df = MagicMock()
    mock_xlsx_processor.return_value._load_document.return_value = mock_df

    engine = load_xlsx_to_db("dummy_path.xlsx", "Sheet1", access_level=3, table_name="test_table")

    mock_xlsx_processor.return_value._load_document.assert_called_once()
    mock_df.__setitem__.assert_called_once_with("access_level", 3)  # Ensure "access_level" is set
    mock_df.to_sql.assert_called_once_with("test_table", con=mock_engine, if_exists="replace", index=False)
    assert engine == mock_engine