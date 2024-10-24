from rag.parsing.processor import FileProcessor
from pathlib import Path
from llama_index.core.prompts import ChatPromptTemplate
from llama_index.core.bridge.pydantic import BaseModel, Field
from llama_index.llms.openai import OpenAI
from llama_index.core.llms import ChatMessage
import pandas as pd

class TableInfo(BaseModel):
    table_name: str = Field(..., description="Unique table name (must use underscores and NO spaces)")
    table_summary: str = Field(..., description="Short, concise summary/caption of the table")

class XLSXProcessor(FileProcessor):
    def __init__(self, document_path, sheet_name=None):
        pass

    def _get_prompt_template(self):
        """Returns the prompt template for table summary generation."""
        pass

    def _load_document(self):
        """Loads the XLSX document into a pandas DataFrame."""
        pass
        
    def _get_table_info(self):
        """Generates table information using the loaded DataFrame and LLM."""
        pass

    def process(self):
        """Main processing method: loads the document and generates table info."""
        pass