from abc import ABC, abstractmethod
from pathlib import Path
from llama_index.readers.file.docs.base import PDFReader
from llama_index.core.node_parser import SentenceSplitter

# Abstract base class
class FileProcessor(ABC):

    @abstractmethod
    def load_document(self):
        """Abstract method to load the document data."""
        pass
    
    @abstractmethod
    def get_nodes(self, documents):
        """Common method for all file types to split content into nodes."""
        pass
    
    @abstractmethod
    def process(self):
        """Processes the document and returns nodes."""
        pass