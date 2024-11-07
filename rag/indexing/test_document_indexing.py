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
    # Mock node with empty metadata
    node = MagicMock()
    node.metadata = {}
    
    # Update the metadata of the node using the _update_metadata method
    updated_node = document_indexing._update_metadata(node, document)
    
    # Assertions to verify metadata updates
    assert updated_node.metadata["id"] == document.id
    assert updated_node.metadata["title"] == document.title
    assert updated_node.metadata["type"] == document.type
    assert updated_node.metadata["object_name"] == document.object_name
    assert updated_node.metadata["created_at"] == document.created_at
    assert updated_node.metadata["updated_at"] == document.updated_at

# Test for the fetch_documents method
@patch("rag.indexing.document_indexing.datetime")
def test_fetch_documents_from_date(mock_datetime, document_indexing):
    # Mock the current datetime to have a consistent result
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

# Test for the process_documents method flow
@patch("rag.indexing.document_indexing.CSVProcessor.process")
@patch("rag.indexing.document_indexing.Document.generate_presigned_url")
def test_process_documents_csv(mock_generate_presigned_url, mock_process, document_indexing, document):
    mock_generate_presigned_url.return_value = "dummy_url"
    mock_process.return_value = pd.DataFrame({"column": [1, 2, 3]})

    document_indexing.fetch_documents = MagicMock(return_value=[document])  # Mock fetch_documents to return a sample document
    document_indexing._store_tabular = MagicMock()  # Mock _store_tabular method

    document_indexing.process_documents()

    mock_generate_presigned_url.assert_called_once()
    document_indexing._store_tabular.assert_called_once()
    mock_process.assert_called_once()

