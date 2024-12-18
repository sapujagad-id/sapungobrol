from datetime import datetime
from unittest.mock import MagicMock, mock_open, patch

import pandas as pd
import pytest

from document.document import Document
from document.service import DocumentServiceV1
from rag.automation.document_automation import DocumentIndexing
from rag.parsing.parsing_csv import CSVProcessor
from rag.parsing.parsing_pdf import PDFProcessor
from rag.parsing.parsing_txt import TXTProcessor


@pytest.fixture
def mock_service():
    return MagicMock(spec=DocumentServiceV1)

# Fixture for a sample Document instance
@pytest.fixture
def document():
    return Document(
        id="f295fafb-829a-49e8-879a-0eb81cc4d3ad",
        title="Test Document",
        type="csv",
        object_name="test.csv",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        access_level=5
    )

@pytest.fixture
def aws_config():
    return MagicMock(
        aws_access_key_id="dummy_access_key",
        aws_secret_access_key="dummy_secret_key",
        aws_region="us-east-1",
        aws_endpoint_url="http://localhost",
        aws_public_bucket_name="dummy_bucket"
    )
# Fixture for DocumentIndexing instance with a mock service
@pytest.fixture
def document_indexing(mock_service, aws_config):
    return DocumentIndexing(aws_config=aws_config, service=mock_service)

def test_s3_client_initialization(document_indexing, aws_config):
    assert document_indexing.s3_client is not None
    assert document_indexing.s3_client.meta.endpoint_url == aws_config.aws_endpoint_url

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

# # Test for the fetch_documents method
@patch("rag.automation.document_automation.datetime", autospec=True)
def test_fetch_documents_from_date(mock_datetime, document_indexing):

    mock_datetime.now.return_value = datetime(2024, 11, 7, 12, 0, 0)

    start_date = datetime(2024, 1, 1)
    filter_criteria = {
        "created_after": start_date.isoformat(),
        "created_before": "2024-11-07T12:00:00"  
    }
    document_indexing.service = MagicMock()
    document_indexing.service.get_documents.return_value = ["Mocked Document"]

    documents = document_indexing.fetch_documents(start_date=start_date)
    document_indexing.service.get_documents.assert_called_once_with(filter=filter_criteria)
    assert documents == ["Mocked Document"]

# # Test for the process_documents method flow with CSV format
@patch("rag.automation.document_automation.CSVProcessor.process")
@patch("rag.automation.document_automation.generate_presigned_url")
@patch("requests.get")  
def test_process_documents_csv(mock_get, mock_generate_presigned_url, mock_process, document_indexing, document):
    mock_generate_presigned_url.return_value = "https://dummy_url"
    mock_process.return_value = pd.DataFrame({"column": [1, 2, 3]})

    mock_response = MagicMock()
    mock_response.content = b"mocked_bytes_content"  
    mock_get.return_value = mock_response

    document_indexing.fetch_documents = MagicMock(return_value=[document])
    document_indexing._store_tabular = MagicMock()

    document_indexing.process_documents()

    mock_generate_presigned_url.assert_called_once()
    document_indexing._store_tabular.assert_called_once()
    mock_process.assert_called_once()

# # # Test for the process_documents method flow with PDF format
@patch("rag.automation.document_automation.PDFProcessor.process")
@patch("document.document.Document.generate_presigned_url")
@patch("requests.get")  
def test_process_documents_pdf(mock_requests_get, mock_generate_presigned_url, mock_pdf_process, document_indexing, document):
 
    mock_generate_presigned_url.return_value = "https://dummy_url"

    mock_requests_get.return_value.content = b"dummy PDF content"
    mock_requests_get.return_value.status_code = 200  

    mock_pdf_process.return_value = [
        MagicMock(text="sample node text 1", metadata={}),
        MagicMock(text="sample node text 2", metadata={})
    ]

    document.type = 'pdf'
    document_indexing.fetch_documents = MagicMock(return_value=[document])
    document_indexing._store_vector = MagicMock()

    document_indexing.process_documents()

    mock_generate_presigned_url.assert_called_once()
    mock_requests_get.assert_called_once_with("https://dummy_url")  
    mock_pdf_process.assert_called_once()
    document_indexing._store_vector.assert_called_once()


# # # Test for the process_documents method flow with TXT format
@patch("rag.automation.document_automation.TXTProcessor.process")
@patch("document.document.Document.generate_presigned_url")
@patch("requests.get")  
def test_process_documents_txt(mock_requests_get, mock_generate_presigned_url, mock_txt_process, document_indexing, document):
    mock_generate_presigned_url.return_value = "https://dummy_url"

    mock_requests_get.return_value.content = b"dummy TXT content"
    mock_requests_get.return_value.status_code = 200  

    mock_txt_process.return_value = [
        MagicMock(text="sample node text 1", metadata={}),
        MagicMock(text="sample node text 2", metadata={})
    ]
    document.type = 'txt'
    document_indexing.fetch_documents = MagicMock(return_value=[document])
    document_indexing._store_vector = MagicMock()
    document_indexing.process_documents()

    mock_generate_presigned_url.assert_called_once()
    mock_requests_get.assert_called_once_with("https://dummy_url")  
    mock_txt_process.assert_called_once()
    document_indexing._store_vector.assert_called_once()

@patch("rag.automation.document_automation.get_postgres_engine")
@patch("pandas.DataFrame.to_sql")
@patch("rag.automation.document_automation.text")
def test_store_tabular(mock_text, mock_to_sql, mock_get_engine, document, document_indexing):
    mock_engine = MagicMock()
    mock_get_engine.return_value = mock_engine
    mock_connection = MagicMock()
    mock_engine.connect.return_value.__enter__.return_value = mock_connection
    mock_text.return_value = "MOCKED_QUERY"

    summary = "This is a test summary."
    data = pd.DataFrame({"column1": [1, 2, 3]})

    instance = document_indexing
    instance._store_tabular("test_table", data, document, summary)

    mock_to_sql.assert_called_once_with("test_table", con=mock_engine, if_exists="replace", index=False)
    assert "access_level" in data.columns
    assert all(data["access_level"] == document.access_level)
    
    mock_text.assert_any_call(
        "CREATE TABLE IF NOT EXISTS metadata_table (\n"
        "    id SERIAL PRIMARY KEY,\n"
        "    document_id VARCHAR NOT NULL,\n"
        "    title VARCHAR,\n"
        "    type VARCHAR,\n"
        "    object_name VARCHAR,\n"
        "    created_at TIMESTAMP,\n"
        "    updated_at TIMESTAMP,\n"
        "    access_level INTEGER,\n"
        "    summary TEXT\n"
        ");"
    )
    mock_connection.execute.assert_any_call("MOCKED_QUERY")

    mock_text.assert_any_call(
        "INSERT INTO metadata_table (document_id, title, type, object_name, created_at, updated_at, access_level, summary)\n"
        "VALUES (:document_id, :title, :type, :object_name, :created_at, :updated_at, :access_level, :summary)\n"
        "ON CONFLICT (document_id) DO UPDATE\n"
        "SET title = EXCLUDED.title,\n"
        "    type = EXCLUDED.type,\n"
        "    object_name = EXCLUDED.object_name,\n"
        "    created_at = EXCLUDED.created_at,\n"
        "    updated_at = EXCLUDED.updated_at,\n"
        "    access_level = EXCLUDED.access_level,\n"
        "    summary = EXCLUDED.summary;"
    )
    mock_connection.execute.assert_any_call(
        "MOCKED_QUERY",
        {
            "document_id": document.id,
            "title": document.title,
            "type": document.type,
            "object_name": document.object_name,
            "created_at": document.created_at,
            "updated_at": document.updated_at,
            "access_level": document.access_level,
            "summary": summary
        }
    )

@patch("os.getenv")
@patch("rag.automation.document_automation.PostgresHandler")
@patch("rag.automation.document_automation.PostgresNodeStorage")
def test_store_vector(mock_postgres_storage, mock_postgres_handler, mock_getenv, document_indexing):
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
    document_indexing._store_vector(mock_nodes, 5)

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

@patch("document.document.Document.generate_presigned_url")
def test_generate_presigned_url(mock_generate_presigned_url):
    _ = Document(
        id="f295fafb-829a-49e8-879a-0eb81cc4d3ad",
        title="Sample Document",
        type="txt",
        object_name="sample.txt",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        access_level=1
    )
    mock_generate_presigned_url.return_value = ""
    url =  mock_generate_presigned_url.return_value
    assert isinstance(url, str), "Expected a string for the presigned URL"
    assert url == "", "Expected the presigned URL to be an empty string in placeholder implementation"

@patch("rag.automation.document_automation.requests.get")
@patch("builtins.open", new_callable=mock_open)
def test_request_url(mock_open, mock_requests_get, document_indexing):
    # Mock the response of requests.get
    mock_response = MagicMock()
    mock_response.content = b"mocked content"
    mock_response.status_code = 200
    mock_requests_get.return_value = mock_response

    # Call the _request_url method
    file_path = document_indexing._request_url("pdf", "https://dummy_url")

    # Verify requests.get was called with the correct URL
    mock_requests_get.assert_called_once_with("https://dummy_url")

    # Verify open was called with the constructed file name
    mock_open.assert_called_once_with("temp.pdf", "wb")

    # Verify file.write was called with the correct content
    mock_open().write.assert_called_once_with(b"mocked content")

    # Ensure the returned path is correct
    assert file_path == "temp.pdf"