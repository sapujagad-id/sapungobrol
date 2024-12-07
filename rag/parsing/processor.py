from abc import ABC, abstractmethod

from llama_index.core.bridge.pydantic import BaseModel, Field


class TableInfo(BaseModel):
    table_name: str = Field(..., description="Unique table name (must use underscores and NO spaces)")
    table_summary: str = Field(..., description="Short, concise summary/caption of the table")

# Abstract base class
class FileProcessor(ABC):

    @abstractmethod
    def _load_document(self):
        """
        Loads the document data.

        This method should be implemented to load the document from a specific source 
        (e.g., file, database, etc.) and prepare it for further processing.

        Raises:
            SomeException: If the document loading fails.
        """
    
    @abstractmethod
    def process(self):
        """
        Processes the loaded document and returns the nodes.

        This method should be implemented to process the loaded document, extract 
        relevant information, and return it as a list of nodes or structured data.

        Returns:
            list: A list of nodes or processed data extracted from the document.
        """
