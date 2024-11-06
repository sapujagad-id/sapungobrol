from unittest.mock import MagicMock, patch

import pytest

from rag.sql.local.local_db_loader import load_csv_to_db, load_xlsx_to_db
from rag.sql.local.local_query_engine import (check_db_data, get_table_schema,
                                              run_query, setup_query_engine)


@pytest.fixture
def mock_csv_processor(mocker):
    """Mock CSVProcessor for testing."""
    mock_processor = mocker.patch('rag.sql.local.local_db_loader.CSVProcessor')
    instance = mock_processor.return_value
    instance._load_document.return_value = MagicMock()
    return instance

@pytest.fixture
def mock_xlsx_processor(mocker):
    """Mock XLSXProcessor for testing."""
    mock_processor = mocker.patch('rag.sql.local.local_db_loader.XLSXProcessor')
    instance = mock_processor.return_value
    instance._load_document.return_value = MagicMock()
    return instance

@pytest.fixture
def mock_inspect(mocker):
    """Mock SQLAlchemy's inspect function."""
    mock_inspector = mocker.patch('rag.sql.local.local_query_engine.inspect')
    mock_inspector.return_value.get_columns.return_value = [
        {'name': 'Disbursement Week', 'type': 'DATETIME'}, 
        {'name': 'Num Loan', 'type': 'BIGINT'}, 
        {'name': 'Total Value Approved', 'type': 'TEXT'}
    ]
    return mock_inspector


@pytest.fixture
def mock_nlsql_query_engine(mocker):
    """Mock the NLSQLTableQueryEngine."""
    mock_query_engine = mocker.patch('rag.sql.local.local_query_engine.NLSQLTableQueryEngine')
    return mock_query_engine.return_value


@pytest.fixture
def mock_engine(mocker):
    """Mock SQLAlchemy create_engine."""
    mock_engine = mocker.patch('rag.sql.local.local_db_loader.create_engine')
    return mock_engine.return_value

@pytest.fixture
def mock_create_engine(mocker):
    """Mock SQLAlchemy create_engine."""
    mock_engine = mocker.patch('rag.sql.local.local_query_engine.create_engine')
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

def test_load_xlsx_to_db(mock_xlsx_processor, mock_engine):
    """Test loading a single CSV into the database."""
    engine = load_xlsx_to_db("dummy_path.xlsx", "Sheet1")

    mock_xlsx_processor._load_document.assert_called_once()

    mock_xlsx_processor._load_document().to_sql.assert_called_once_with(
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

    assert schema == ['Disbursement Week (DATETIME)', 'Num Loan (BIGINT)', 'Total Value Approved (TEXT)']
    
def test_setup_query_engine(mock_nlsql_query_engine):
    """Test the setup_query_engine function."""

    query_engine, table_schema = setup_query_engine()

    assert query_engine == mock_nlsql_query_engine
    assert table_schema == [
      'Disbursement Week (TEXT)', 'Num Loan (BIGINT)', 'Total Value Approved (TEXT)', 
      'Total Admin Fee Nett (TEXT)' ,'Total Management Fee Nett (TEXT)', 'Total Gmv (TEXT)',
      'Total Gp (TEXT)'
      ]
    
def test_check_db_data(mock_create_engine, mock_connection):
    """Test checking the database data."""
    check_db_data()
    
    mock_connection.execute.return_value.fetchmany.assert_called_once_with(10)
    
def test_run_query(mock_nlsql_query_engine):
    """Test running a query."""
    
    mock_nlsql_query_engine.query.return_value = MagicMock(response="Mocked response")
    
    with patch('rag.sql.local.local_query_engine.setup_query_engine') as mock_setup_query_engine:
        mock_setup_query_engine.return_value = (
            mock_nlsql_query_engine,
            ['Disbursement Week (DATETIME)', 'Num Loan (BIGINT)', 'Total Value Approved (TEXT)']
        )

        query_str = "What is the total value approved for the week of September 23, 2024?"

        response = run_query(query_str)

        assert response == "Mocked response"
        mock_nlsql_query_engine.query.assert_called_once()

        expected_prompt = """
    You are querying a table with the following columns: 
    Disbursement Week (DATETIME), Num Loan (BIGINT), Total Value Approved (TEXT).
    
    When generating SQL queries, note that the table is in an SQLite database. In SQLite, column names containing spaces must be enclosed in double quotes. Also, be wary of SQL injection attacks. Make sure that the query is not malicious.
    If a date is specified and the column type is DATETIME, use the DATE function just in case the DATETIME entry also contains microseconds. Otherwise, if the column type is TEXT, just use the human format of the date.

    Based on this, generate a SQL query to retrieve the data.

    Question: What is the total value approved for the week of September 23, 2024?
    """.strip()

        actual_prompt = mock_nlsql_query_engine.query.call_args[0][0].strip()

        assert actual_prompt == expected_prompt
