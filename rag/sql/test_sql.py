from unittest.mock import MagicMock, patch

import pytest

from rag.sql.db_loader import load_csv_to_db
from rag.sql.query_engine import get_table_schema, setup_query_engine, check_db_data


@pytest.fixture
def mock_csv_processor(mocker):
    """Mock CSVProcessor for testing."""
    mock_processor = mocker.patch('rag.sql.db_loader.CSVProcessor')
    instance = mock_processor.return_value
    instance._load_document.return_value = MagicMock()
    return instance
  
@pytest.fixture
def mock_inspect(mocker):
    """Mock SQLAlchemy's inspect function."""
    mock_inspector = mocker.patch('rag.sql.query_engine.inspect')
    mock_inspector.return_value.get_columns.return_value = [
        {'name': 'Disbursement Week'}, 
        {'name': 'Num Loan'}, 
        {'name': 'Total Value Approved'}
    ]
    return mock_inspector
  
@pytest.fixture
def mock_openai(mocker):
    """Mock the OpenAI model."""
    mock_openai = mocker.patch('rag.sql.query_engine.OpenAI')
    return mock_openai.return_value


@pytest.fixture
def mock_create_engine(mocker):
    """Mock the SQLAlchemy create_engine function."""
    mock_engine = mocker.patch('rag.sql.query_engine.create_engine')
    return mock_engine.return_value


@pytest.fixture
def mock_sql_database(mocker):
    """Mock the SQLDatabase object."""
    mock_sql_database = mocker.patch('rag.sql.query_engine.SQLDatabase')
    return mock_sql_database.return_value


@pytest.fixture
def mock_nlsql_query_engine(mocker):
    """Mock the NLSQLTableQueryEngine."""
    mock_query_engine = mocker.patch('rag.sql.query_engine.NLSQLTableQueryEngine')
    return mock_query_engine.return_value


@pytest.fixture
def mock_get_table_schema(mocker):
    """Mock the get_table_schema function."""
    mock_schema = mocker.patch('rag.sql.query_engine.get_table_schema')
    mock_schema.return_value = ['Disbursement Week', 'Num Loan', 'Total Value Approved']
    return mock_schema


@pytest.fixture
def mock_engine(mocker):
    """Mock SQLAlchemy create_engine."""
    mock_engine = mocker.patch('rag.sql.db_loader.create_engine')
    return mock_engine.return_value

@pytest.fixture
def mock_create_engine(mocker):
    """Mock SQLAlchemy create_engine."""
    mock_engine = mocker.patch('rag.sql.query_engine.create_engine')
    return mock_engine.return_value


@pytest.fixture
def mock_connection(mock_create_engine):
    """Mock the engine connection and result set."""
    mock_connection = MagicMock()
    mock_create_engine.connect.return_value.__enter__.return_value = mock_connection
    
    # Mock the result of executing a query
    mock_connection.execute.return_value.fetchmany.return_value = [
        ('October 7, 2024', 57, '14,618,341,249'),
        ('September 30, 2024', 168, '28,664,555,477'),
        ('September 23, 2024', 279, '33,296,281,086')
    ]
    
    return mock_connection


def test_load_csv_to_db(mock_csv_processor, mock_engine):
    """Test loading a single CSV into the database."""
    engine = load_csv_to_db("dummy_path.csv")

    mock_csv_processor._load_document.assert_called_once()

    mock_csv_processor._load_document().to_sql.assert_called_once_with(
        'ppl_data', con=mock_engine, if_exists='replace', index=False
    )
    
    assert engine == mock_engine

def test_get_table_schema(mock_inspect):
    """Test fetching the table schema."""
    mock_engine = MagicMock()

    table_name = "ppl_data"
    schema = get_table_schema(mock_engine, table_name)

    mock_inspect.assert_called_once_with(mock_engine)

    mock_inspect.return_value.get_columns.assert_called_once_with(table_name)

    assert schema == ['Disbursement Week', 'Num Loan', 'Total Value Approved']
    
def test_setup_query_engine(mock_nlsql_query_engine):
    """Test the setup_query_engine function."""

    query_engine, table_schema = setup_query_engine()

    assert query_engine == mock_nlsql_query_engine
    assert table_schema == [
      'Disbursement Week', 'Num Loan', 'Total Value Approved', 
      'Total Admin Fee Nett' ,'Total Management Fee Nett', 'Total Gmv',
      'Total Gp'
      ]
    
def test_check_db_data(mock_create_engine, mock_connection):
    """Test checking the database data."""
    check_db_data()
    
    mock_connection.execute.return_value.fetchmany.assert_called_once_with(10)