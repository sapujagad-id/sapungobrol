from rag.parsing.parsing_csv import CSVProcessor
from rag.parsing.parsing_txt import TXTProcessor
from rag.parsing.parsing_pdf import PDFProcessor
#from document.service import DocumentService
import pandas as pd

# WILL DELETE LATER
class Document:
    def __init__(self, id, name, type, object_url, created_at, updated_at):
        self.id = id
        self.name = name
        self.type = type
        self.object_url = object_url
        self.created_at = created_at
        self.updated_at = updated_at

    def generate_presigned_url(self) -> str:
        # Placeholder method to generate a presigned URL
        return self.object_url  # Example implementation

class DocumentIndexing:
    def __init__(self):
        # self.service = DocumentService()
        pass

    def fetch_documents(self) -> list[Document]:
        # Example: return self.service.get_documents(filter={})  # Implement actual fetch logic
        return []

    def _get_processor(self, document_type: str, document_url: str):
        """Returns the appropriate processor based on document type."""
        processors = {
            'csv': CSVProcessor,
            'pdf': PDFProcessor,
            'txt': TXTProcessor,
        }
        processor_class = processors.get(document_type)
        if processor_class:
            return processor_class(document_url)
        raise ValueError(f"Unsupported document type: {document_type}")

    def _update_metadata(self, node, document: Document):
        """Updates metadata of a node based on document properties."""
        node.metadata.update({
            'id': document.id,
            'name': document.name,
            'type': document.type,
            'object_url': document.object_url,
            'created_at': document.created_at,
            'updated_at': document.updated_at
        })
        return node

    def process_documents(self):
        """Main method to process documents based on their type."""
        documents = self.fetch_documents()
        
        for document in documents:
            document_url = document.generate_presigned_url()
            processor = self._get_processor(document.type, document_url)
            
            if document.type == 'csv':
                summary = processor.process()
                data = processor.df
                self._store_tabular(data, summary)

            else:
                nodes = processor.process()
                nodes = [self._update_metadata(node, document) for node in nodes]
                self._store_vector(nodes)

    def _store_tabular(self, data: pd.DataFrame, summary: str):
        # Implement logic to store tabular data and summary
        pass

    def _store_vector(self, nodes):
        # Implement logic to store vector data
        pass