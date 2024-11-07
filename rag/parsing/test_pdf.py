import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from rag.parsing.parsing_pdf import PDFProcessor

@pytest.fixture
def mock_pdf_reader(mocker):
    """Mock the PDFReader."""
    mock_pdf_reader = mocker.patch('rag.parsing.parsing_pdf.PDFReader')
    instance = mock_pdf_reader.return_value
    instance.load_data.return_value = ["Mocked Document Content"]
    return instance

@pytest.fixture
def mock_sentence_splitter(mocker):
    """Mock the SentenceSplitter."""
    mock_sentence_splitter = mocker.patch('rag.parsing.parsing_pdf.SentenceSplitter')
    instance = mock_sentence_splitter.return_value
    instance.get_nodes_from_documents.return_value = ["Mocked Node"]
    return instance

def test_pdf_processor_init(mock_pdf_reader, mock_sentence_splitter):
    """Test the initialization of PDFProcessor."""
    processor = PDFProcessor(chunk_size=100, chunk_overlap=10)
    assert processor.chunk_size == 100
    assert processor.chunk_overlap == 10
    assert processor.pdf_reader == mock_pdf_reader
    assert processor.splitting_parser == mock_sentence_splitter

def test_load_document(mock_pdf_reader):
    """Test the _load_document method."""
    processor = PDFProcessor()
    processor.document_path = "dummy_path"  # Set document path for the test
    result = processor._load_document()
    assert result == ["Mocked Document Content"]
    mock_pdf_reader.load_data.assert_called_once_with(file="dummy_path")

def test_get_nodes(mock_sentence_splitter):
    """Test the get_nodes method."""
    processor = PDFProcessor()
    documents = ["Mocked Document Content"]
    result = processor.get_nodes(documents)
    assert result == ["Mocked Node"]
    mock_sentence_splitter.get_nodes_from_documents.assert_called_once_with(documents=documents)

def test_process(mock_pdf_reader, mock_sentence_splitter):
    """Test the process method, which integrates loading and splitting."""
    processor = PDFProcessor()
    result = processor.process("dummy_path")
    assert result == ["Mocked Node"]
    mock_pdf_reader.load_data.assert_called_once_with(file="dummy_path")
    mock_sentence_splitter.get_nodes_from_documents.assert_called_once_with(documents=["Mocked Document Content"])

def test_load_document_exception(mock_pdf_reader):
    """Test the _load_document method when an exception is raised."""
    mock_pdf_reader.load_data.side_effect = Exception("PDF loading error")
    processor = PDFProcessor()
    processor.document_path = "dummy_path"
    with pytest.raises(RuntimeError, match="Failed to load document: PDF loading error"):
        processor._load_document()

def test_get_nodes_exception(mock_sentence_splitter):
    """Test the get_nodes method when an exception is raised."""
    mock_sentence_splitter.get_nodes_from_documents.side_effect = Exception("Node extraction error")
    processor = PDFProcessor()
    documents = ["Mocked Document Content"]
    with pytest.raises(RuntimeError, match="Failed to get nodes from documents: Node extraction error"):
        processor.get_nodes(documents)
