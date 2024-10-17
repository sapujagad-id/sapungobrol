import pytest
from unittest.mock import MagicMock
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
    processor = PDFProcessor("dummy_path", chunk_size=100, chunk_overlap=10)
    assert processor.document_path == Path("dummy_path")
    assert processor.chunk_size == 100
    assert processor.chunk_overlap == 10
    assert processor.pdf_reader == mock_pdf_reader
    assert processor.splitting_parser == mock_sentence_splitter

def test_load_document(mock_pdf_reader):
    """Test the load_document method."""
    processor = PDFProcessor("dummy_path")
    result = processor.load_document()
    assert result == ["Mocked Document Content"]
    mock_pdf_reader.load_data.assert_called_once_with(file=Path("dummy_path"))

def test_get_nodes(mock_sentence_splitter):
    """Test the get_nodes method."""
    processor = PDFProcessor("dummy_path")
    documents = ["Mocked Document Content"]
    result = processor.get_nodes(documents)
    assert result == ["Mocked Node"]
    mock_sentence_splitter.get_nodes_from_documents.assert_called_once_with(documents=documents)

def test_process(mock_pdf_reader, mock_sentence_splitter):
    """Test the process method, which integrates loading and splitting."""
    processor = PDFProcessor("dummy_path")
    result = processor.process()
    assert result == ["Mocked Node"]
    mock_pdf_reader.load_data.assert_called_once_with(file=Path("dummy_path"))
    mock_sentence_splitter.get_nodes_from_documents.assert_called_once_with(documents=["Mocked Document Content"])
