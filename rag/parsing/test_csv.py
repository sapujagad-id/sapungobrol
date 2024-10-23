import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import pandas as pd
from rag.parsing.parsing_csv import CSVProcessor, TableInfo

@pytest.fixture
def mock_openai_llm(mocker):
    """Fixture to mock the OpenAI LLM."""
    mock_openai = mocker.patch('rag.parsing.parsing_csv.OpenAI')
    instance = mock_openai.return_value
    instance.structured_predict.return_value = TableInfo(
        table_name="mocked_table",
        table_summary="Mocked table summary."
    )
    return instance

@pytest.fixture
def mock_csv_data(mocker):
    """Fixture to mock the pandas read_csv function."""
    mocker.patch('pandas.read_csv', return_value=pd.DataFrame({
        'col1': [1, 2],
        'col2': [3, 4]
    }))

def test_csv_processor_init(mock_openai_llm):
    """Test the initialization of CSVProcessor."""
    processor = CSVProcessor("dummy_path")
    assert processor.document_path == Path("dummy_path")
    assert processor.df is None
    assert processor.llm == mock_openai_llm

def test_load_document(mock_csv_data):
    """Test the _load_document method."""
    processor = CSVProcessor("dummy_path")
    df = processor._load_document()
    assert isinstance(df, pd.DataFrame)
    assert 'col1' in df.columns
    assert 'col2' in df.columns

def test_load_document_failure(mocker):
    """Test load_document raises an exception when loading fails."""
    mocker.patch('pandas.read_csv', side_effect=Exception("CSV loading error"))
    processor = CSVProcessor("dummy_path")
    with pytest.raises(RuntimeError, match="Failed to load document: CSV loading error"):
        processor._load_document()

def test_get_table_info(mock_openai_llm, mock_csv_data):
    """Test the _get_table_info method."""
    processor = CSVProcessor("dummy_path")
    processor.df = pd.DataFrame({'col1': [1, 2], 'col2': [3, 4]})
    
    table_info = processor._get_table_info()
    
    # Ensure the correct call was made to the LLM
    mock_openai_llm.structured_predict.assert_called_once()
    
    # Validate the returned table info
    assert table_info.table_name == "mocked_table"
    assert table_info.table_summary == "Mocked table summary."

def test_process(mock_openai_llm, mock_csv_data):
    """Test the process method that integrates loading and generating table info."""
    processor = CSVProcessor("dummy_path")
    table_info = processor.process()
    
    # Ensure the table info was generated
    assert table_info.table_name == "mocked_table"
    assert table_info.table_summary == "Mocked table summary."
    
    # Ensure that the document was loaded and table info was generated
    mock_openai_llm.structured_predict.assert_called_once()

def test_get_table_info_no_df():
    """Test _get_table_info raises a RuntimeError when DataFrame is not loaded."""
    processor = CSVProcessor("dummy_path")
    processor.df = None  # Ensure that df is not loaded
    with pytest.raises(RuntimeError, match="DataFrame is not loaded."):
        processor._get_table_info()
