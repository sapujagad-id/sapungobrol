import pytest
from unittest.mock import MagicMock
from pathlib import Path
from rag.parsing.parsing_pdf import PDFProcessor
from llama_index.core import Document

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

@pytest.fixture
def mock_sentence_splitter(mocker):
    """Mock the SentenceSplitter."""
    mock_sentence_splitter = mocker.patch('rag.parsing.parsing_pdf.SentenceSplitter')
    instance = mock_sentence_splitter.return_value
    instance.get_nodes_from_documents.return_value = ["Mocked Node"]
    return instance

@pytest.fixture
def mock_ocr_reader(mocker):
    """Mock the OCR reader."""
    mock_ocr_reader = mocker.patch('rag.parsing.parsing_pdf.easyocr.Reader')
    instance = mock_ocr_reader.return_value
    instance.readtext.return_value = ["Mocked OCR Text"]
    return instance

@pytest.fixture
def mock_pdf_to_image(mocker):
    """Mock the pdf2image convert_from_path."""
    mock_convert_from_path = mocker.patch('rag.parsing.parsing_pdf.convert_from_path')
    mock_convert_from_path.return_value = ["Mocked Image"]
    return mock_convert_from_path

@pytest.fixture
def mock_numpy_array(mocker):
    """Mock the numpy array conversion."""
    mock_np_array = mocker.patch('rag.parsing.parsing_pdf.np.array')
    mock_np_array.return_value = "Mocked Numpy Array"
    return mock_np_array


def test_pdf_processor_init(mock_pdf_reader, mock_sentence_splitter):
    """Test the initialization of PDFProcessor."""
    processor = PDFProcessor("dummy_path", chunk_size=100, chunk_overlap=10)
    assert processor.document_path == Path("dummy_path")
    assert processor.chunk_size == 100
    assert processor.chunk_overlap == 10
    assert processor.pdf_reader == mock_pdf_reader
    assert processor.splitting_parser == mock_sentence_splitter

def test_load_document(mock_pdf_reader, mock_ocr_reader, mock_pdf_to_image, mock_numpy_array):
    """Test the _load_document method."""
    mock_pdf_reader.load_data.return_value = [{"text": "Mocked Document Content"}]
    mock_ocr_reader.readtext.return_value = ["Mocked OCR Text"]
    
    processor = PDFProcessor("dummy_path")
    result = processor._load_document()
    
    expected_text = "Extracted Text:\nMocked Document Content\n\nOCR Text:\nPage 1 OCR Text:\n['Mocked OCR Text']"
    expected_document = [Document(text=expected_text, id_="dummy_path")]
    
    assert result == expected_document

def test_get_nodes(mock_sentence_splitter):
    """Test the get_nodes method."""
    processor = PDFProcessor("dummy_path")
    documents = ["Mocked Document Content"]
    result = processor.get_nodes(documents)
    assert result == ["Mocked Node"]
    mock_sentence_splitter.get_nodes_from_documents.assert_called_once_with(documents=documents)

def test_process(mock_pdf_reader, mock_sentence_splitter, mock_ocr_reader, mock_pdf_to_image, mock_numpy_array):
    """Test the process method."""
    processor = PDFProcessor("dummy_path")
    result = processor.process()
    assert result == ["Mocked Node"]
    
def test_load_document_exception(mock_pdf_reader):
    """Test the load_document method when an exception is raised."""
    mock_pdf_reader.load_data.side_effect = Exception("PDF loading error")
    processor = PDFProcessor("dummy_path")
    with pytest.raises(RuntimeError, match="Failed to load document: PDF loading error"):
        processor._load_document()

def test_get_nodes_exception(mock_sentence_splitter):
    """Test the get_nodes method when an exception is raised."""
    mock_sentence_splitter.get_nodes_from_documents.side_effect = Exception("Node extraction error")
    processor = PDFProcessor("dummy_path")
    documents = ["Mocked Document Content"]
    with pytest.raises(RuntimeError, match="Failed to get nodes from documents: Node extraction error"):
        processor.get_nodes(documents)

