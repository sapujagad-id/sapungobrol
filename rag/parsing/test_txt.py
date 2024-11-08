import pytest
from unittest.mock import MagicMock
from pathlib import Path
from rag.parsing.processor import FileProcessor
from rag.parsing.parsing_txt import TXTProcessor  # Adjust import based on your project structure

@pytest.fixture
def mock_simple_directory_reader(mocker):
    """Mock the SimpleDirectoryReader."""
    mock_reader_class = mocker.patch('rag.parsing.parsing_txt.SimpleDirectoryReader')
    mock_reader_instance = mock_reader_class.return_value  # Mock the instance created by SimpleDirectoryReader()
    mock_reader_instance.load_data.return_value = ["Mocked Document Content"]
    return mock_reader_instance

@pytest.fixture
def mock_sentence_splitter(mocker):
    """Mock the SentenceSplitter."""
    mock_splitter = mocker.patch('rag.parsing.parsing_txt.SentenceSplitter')
    instance = mock_splitter.return_value
    instance.get_nodes_from_documents.return_value = ["Mocked Node"]
    return instance

def test_txt_processor_init(mock_simple_directory_reader, mock_sentence_splitter):
    """Test the initialization of TXTProcessor."""
    processor = TXTProcessor("dummy_path", chunk_size=200, chunk_overlap=0)
    assert processor.document_path == Path("dummy_path")
    assert processor.chunk_size == 200
    assert processor.chunk_overlap == 0
    assert processor.splitting_parser == mock_sentence_splitter

def test_load_document(mock_simple_directory_reader):
    """Test the _load_document method."""
    processor = TXTProcessor("dummy_path")
    result = processor._load_document()
    assert result == ["Mocked Document Content"]
    # Verify that SimpleDirectoryReader was called with the correct arguments
    processor_instance = mock_simple_directory_reader  # Already a mock instance
    processor_instance.load_data.assert_called_once()

def test_get_nodes(mock_sentence_splitter):
    """Test the get_nodes method."""
    processor = TXTProcessor("dummy_path")
    documents = ["Mocked Document Content"]
    result = processor.get_nodes(documents)
    assert result == ["Mocked Node"]
    mock_sentence_splitter.get_nodes_from_documents.assert_called_once_with(documents=documents)

def test_process(mock_simple_directory_reader, mock_sentence_splitter):
    """Test the process method, which integrates loading and splitting."""
    processor = TXTProcessor("dummy_path")
    result = processor.process()
    assert result == ["Mocked Node"]
    mock_simple_directory_reader.load_data.assert_called_once()
    mock_sentence_splitter.get_nodes_from_documents.assert_called_once_with(documents=["Mocked Document Content"])

def test_load_document_exception(mock_simple_directory_reader):
    """Test the _load_document method when an exception is raised."""
    mock_simple_directory_reader.load_data.side_effect = Exception("Document loading error")
    processor = TXTProcessor("dummy_path")
    with pytest.raises(RuntimeError, match="Failed to load document: Document loading error"):
        processor._load_document()

def test_get_nodes_exception(mock_sentence_splitter):
    """Test the get_nodes method when an exception is raised."""
    mock_sentence_splitter.get_nodes_from_documents.side_effect = Exception("Node extraction error")
    processor = TXTProcessor("dummy_path")
    documents = ["Mocked Document Content"]
    with pytest.raises(RuntimeError, match="Failed to get nodes from documents: Node extraction error"):
        processor.get_nodes(documents)