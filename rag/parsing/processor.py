from abc import ABC, abstractmethod
from llama_index.core.bridge.pydantic import BaseModel, Field

class TableInfo(BaseModel):
    table_name: str = Field(..., description="Unique table name (must use underscores and NO spaces)")
    table_summary: str = Field(..., description="Short, concise summary/caption of the table")

# Abstract base class
class FileProcessor(ABC):

    @abstractmethod
    def _load_document(self):
        """Abstract method to load the document data."""
    
    @abstractmethod
    def process(self):
        """Processes the document and returns nodes."""
