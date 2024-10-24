import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import pandas as pd
from rag.parsing.parsing_xlsx import XLSXProcessor, TableInfo

@pytest.fixture
def mock_openai_llm(mocker):
    """Fixture to mock the OpenAI LLM."""
    mock_openai = mocker.patch('rag.parsing.parsing_xlsx.OpenAI')
    instance = mock_openai.return_value
    instance.structured_predict.return_value = TableInfo(
        table_name="mocked_table",
        table_summary="Mocked table summary."
    )
    return instance

@pytest.fixture
def mock_xlsx_data(mocker):
    """Fixture to mock the pandas read_excel function."""
    mocker.patch('pandas.read_excel', return_value=pd.DataFrame({
        'col1': [1, 2],
        'col2': [3, 4]
    }))

def test_xlsx_processor_init(mock_openai_llm):
    """Test the initialization of XLSXProcessor."""
    processor = XLSXProcessor("dummy_path.xlsx", sheet_name="Sheet1")
    
    assert processor.document_path == Path("dummy_path.xlsx")
    assert processor.df is None
    assert processor.llm == mock_openai_llm
    assert processor.sheet_name == "Sheet1"

def test_load_document(mock_xlsx_data):
    """Test the _load_document method for XLSX."""
    processor = XLSXProcessor("dummy_path.xlsx")
    df = processor._load_document()
    
    assert isinstance(df, pd.DataFrame)
    assert 'col1' in df.columns
    assert 'col2' in df.columns

def test_load_document_non_existent_file(mocker):
    """Test _load_document raises an exception when loading non-existent file."""
    mocker.patch('pandas.read_excel', side_effect=FileNotFoundError)
    
    processor = XLSXProcessor("non_existent_file.xlsx", sheet_name="Sheet1")
    
    with pytest.raises(RuntimeError, match="File not found: non_existent_file.xlsx"):
        processor._load_document()

def test_load_document_non_existent_sheet(mocker):
    """Test the _load_document method raises an error for a non-existent sheet."""
    mocker.patch('pandas.read_excel', side_effect=ValueError("Worksheet named 'NonExistentSheet' not found"))
    
    processor = XLSXProcessor("dummy_path.xlsx", sheet_name="NonExistentSheet")
    
    with pytest.raises(RuntimeError, match="Sheet 'NonExistentSheet' not found in the file: dummy_path.xlsx"):
        processor._load_document()

def test_load_document_general_error(mocker):
    """Test the _load_document method raises a general error for unexpected exceptions."""
    mocker.patch('pandas.read_excel', side_effect=Exception("Unexpected error"))
    
    processor = XLSXProcessor("dummy_path.xlsx", sheet_name="Sheet1")
    
    with pytest.raises(RuntimeError, match="Failed to load document due to an unexpected error: Unexpected error"):
        processor._load_document()

def test_get_table_info(mock_openai_llm, mock_xlsx_data):
    """Test the _get_table_info method."""
    processor = XLSXProcessor("dummy_path.xlsx")
    processor.df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
    
    table_info = processor._get_table_info()
    
    mock_openai_llm.structured_predict.assert_called_once()
    
    assert table_info.table_name == "mocked_table"
    assert table_info.table_summary == "Mocked table summary."

def test_process(mock_openai_llm, mock_xlsx_data):
    """Test the process method that integrates loading and generating table info."""
    processor = XLSXProcessor("dummy_path.xlsx")
    table_info = processor.process()
    
    assert table_info.table_name == "mocked_table"
    assert table_info.table_summary == "Mocked table summary."
    
    mock_openai_llm.structured_predict.assert_called_once()

def test_get_table_info_no_df():
    """Test _get_table_info raises a RuntimeError when DataFrame is not loaded."""
    processor = XLSXProcessor("dummy_path.xlsx")
    processor.df = None
    
    with pytest.raises(RuntimeError, match="DataFrame is not loaded."):
        processor._get_table_info()
