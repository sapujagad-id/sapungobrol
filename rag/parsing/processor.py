from abc import ABC, abstractmethod

# Abstract base class
class FileProcessor(ABC):

    @abstractmethod
    def _load_document(self):
        """Abstract method to load the document data."""
        pass
    
    @abstractmethod
    def process(self):
        """Processes the document and returns nodes."""
        pass