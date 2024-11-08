import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from rag.parsing.parsing_csv import CSVProcessor
from rag.parsing.parsing_pdf import PDFProcessor
from rag.parsing.parsing_txt import TXTProcessor
from rag.indexing.document_indexing import DocumentIndexing, Document
import pandas as pd
# Fixture for a sample Document instance
@pytest.fixture
def document():
    return Document(
        id="123",
        title="Test Document",
        type="csv",
        object_name="test.csv",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

# Fixture for DocumentIndexing instance with a mock service
@pytest.fixture
def document_indexing():
    indexing = DocumentIndexing()
    indexing.service = MagicMock()  # Mocking the DocumentServiceV1 dependency
    return indexing

# Test for the _get_processor method
def test_get_processor_csv(document_indexing):
    processor = document_indexing._get_processor("csv", "dummy_url")
    assert isinstance(processor, CSVProcessor)

def test_get_processor_pdf(document_indexing):
    processor = document_indexing._get_processor("pdf", "dummy_url")
    assert isinstance(processor, PDFProcessor)

def test_get_processor_txt(document_indexing):
    processor = document_indexing._get_processor("txt", "dummy_url")
    assert isinstance(processor, TXTProcessor)

def test_get_processor_invalid(document_indexing):
    with pytest.raises(ValueError, match="Unsupported document type: docx"):
        document_indexing._get_processor("docx", "dummy_url")

# Test for the _update_metadata method
def test_update_metadata(document_indexing, document):
    node = MagicMock()
    node.metadata = {}
    
    updated_node = document_indexing._update_metadata(node, document)
    
    assert updated_node.metadata["id"] == document.id
    assert updated_node.metadata["title"] == document.title
    assert updated_node.metadata["type"] == document.type
    assert updated_node.metadata["object_name"] == document.object_name
    assert updated_node.metadata["created_at"] == document.created_at
    assert updated_node.metadata["updated_at"] == document.updated_at

# Test for the fetch_documents method
@patch("rag.indexing.document_indexing.datetime")
def test_fetch_documents_from_date(mock_datetime, document_indexing):
    mock_datetime.now.return_value = datetime(2024, 11, 7, 12, 0, 0)
    start_date = datetime(2024, 1, 1)
    filter_criteria = {
        "created_after": start_date.isoformat(),
        "created_before": "2024-11-07T12:00:00"
    }
    document_indexing.service.get_documents.return_value = ["Mocked Document"]
    
    documents = document_indexing.fetch_documents(start_date=start_date)
    document_indexing.service.get_documents.assert_called_once_with(filter=filter_criteria)
    assert documents == ["Mocked Document"]

# Test for the process_documents method flow with CSV format
@patch("rag.indexing.document_indexing.CSVProcessor.process")
@patch("rag.indexing.document_indexing.Document.generate_presigned_url")
def test_process_documents_csv(mock_generate_presigned_url, mock_process, document_indexing, document):
    mock_generate_presigned_url.return_value = "dummy_url"
    mock_process.return_value = pd.DataFrame({"column": [1, 2, 3]})

    document_indexing.fetch_documents = MagicMock(return_value=[document])
    document_indexing._store_tabular = MagicMock()

    document_indexing.process_documents()

    mock_generate_presigned_url.assert_called_once()
    document_indexing._store_tabular.assert_called_once()
    mock_process.assert_called_once()

# Test for the process_documents method flow with PDF format
@patch("rag.indexing.document_indexing.PDFProcessor.process")
@patch("rag.indexing.document_indexing.Document.generate_presigned_url")
def test_process_documents_pdf(mock_generate_presigned_url, mock_pdf_process, document_indexing, document):
    mock_generate_presigned_url.return_value = "dummy_url"
    mock_pdf_process.return_value = [
        MagicMock(text="sample node text 1", metadata={}),
        MagicMock(text="sample node text 2", metadata={})
    ]

    document.type = 'pdf'
    document_indexing.fetch_documents = MagicMock(return_value=[document])
    document_indexing._store_vector = MagicMock()

    document_indexing.process_documents()

    mock_generate_presigned_url.assert_called_once()
    mock_pdf_process.assert_called_once()
    document_indexing._store_vector.assert_called_once()

# Test for the process_documents method flow with TXT format
@patch("rag.indexing.document_indexing.TXTProcessor.process")
@patch("rag.indexing.document_indexing.Document.generate_presigned_url")
def test_process_documents_txt(mock_generate_presigned_url, mock_txt_process, document_indexing, document):
    mock_generate_presigned_url.return_value = "dummy_url"
    mock_txt_process.return_value = [
        MagicMock(text="sample node text 1", metadata={}),
        MagicMock(text="sample node text 2", metadata={})
    ]

    document.type = 'txt'
    document_indexing.fetch_documents = MagicMock(return_value=[document])
    document_indexing._store_vector = MagicMock()

    document_indexing.process_documents()

    mock_generate_presigned_url.assert_called_once()
    mock_txt_process.assert_called_once()
    document_indexing._store_vector.assert_called_once()

@patch("rag.indexing.document_indexing.get_postgres_engine")
@patch("pandas.DataFrame.to_sql")
def test_store_tabular(mock_to_sql, mock_get_postgres_engine):
    mock_engine = MagicMock()
    mock_get_postgres_engine.return_value = mock_engine

    data = pd.DataFrame({"column1": [1, 2, 3]})
    table_name = "test_table"
    summary = "This is a summary of the data."

    document_indexing = DocumentIndexing()
    document_indexing._store_tabular(table_name, data, summary)

    assert "access_level" in data.columns
    assert all(data["access_level"] == 5)

    mock_get_postgres_engine.assert_called_once()

    mock_to_sql.assert_called_once_with(
        table_name, con=mock_engine, if_exists="replace", index=False
    )

@patch("os.getenv")
@patch("rag.indexing.document_indexing.PostgresHandler")
@patch("rag.indexing.document_indexing.PostgresNodeStorage")
def test_store_vector(mock_postgres_storage, mock_postgres_handler, mock_getenv):
    mock_getenv.side_effect = lambda key, default=None: {
        "POSTGRES_DB": "test_db",
        "POSTGRES_USER": "test_user",
        "POSTGRES_PASSWORD": "test_password",
        "POSTGRES_HOST": "localhost",
        "POSTGRES_PORT": "5432"
    }.get(key, default)

    mock_nodes = [MagicMock(text="node text 1"), MagicMock(text="node text 2")]
    
    mock_handler_instance = mock_postgres_handler.return_value
    mock_storage_instance = mock_postgres_storage.return_value

    document_indexing = DocumentIndexing()
    document_indexing._store_vector(mock_nodes)

    mock_postgres_handler.assert_called_once_with(
        db_name="test_db",
        user="test_user",
        password="test_password",
        host="localhost",
        port=5432,
        dimension=1536
    )
    mock_postgres_storage.assert_called_once_with(mock_handler_instance)

    mock_storage_instance.store_nodes.assert_called_once_with(
        ["node text 1", "node text 2"], 5
    )

    mock_handler_instance.close.assert_called_once()