import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from rag.parsing.parsing_csv import CSVProcessor
from rag.parsing.parsing_pdf import PDFProcessor
from rag.parsing.parsing_txt import TXTProcessor
from rag.indexing.document_indexing import DocumentIndexing, Document
import pandas as pd

# Mocking the necessary methods and classes
@pytest.fixture
def document():
    return Document(
        id="123",
        name="Test Document",
        type="csv",
        object_url="test.csv",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

@pytest.fixture
def document_indexing():
    return DocumentIndexing()

# Test for _get_processor method
def test_get_processor_csv(document_indexing, document):
    processor = document_indexing._get_processor("csv", document.object_url)
    assert isinstance(processor, CSVProcessor)

def test_get_processor_pdf(document_indexing, document):
    processor = document_indexing._get_processor("pdf", document.object_url)
    assert isinstance(processor, PDFProcessor)

def test_get_processor_txt(document_indexing, document):
    processor = document_indexing._get_processor("txt", document.object_url)
    assert isinstance(processor, TXTProcessor)

def test_get_processor_invalid(document_indexing, document):
    with pytest.raises(ValueError):
        document_indexing._get_processor("docx", document.object_url)

# Test for _update_metadata method
def test_update_metadata(document_indexing, document):
    # Create a mock node object
    node = MagicMock()
    
    node.metadata = {}
    
    # Update the metadata of the node using the method
    updated_node = document_indexing._update_metadata(node, document)
    
    assert updated_node.metadata["id"] == document.id
    assert updated_node.metadata["name"] == document.name
    assert updated_node.metadata["type"] == document.type
    assert updated_node.metadata["object_url"] == document.object_url
    assert updated_node.metadata["created_at"] == document.created_at
    assert updated_node.metadata["updated_at"] == document.updated_at
