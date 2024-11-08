from rag.parsing.parsing_csv import CSVProcessor
from rag.parsing.parsing_txt import TXTProcessor
from rag.parsing.parsing_pdf import PDFProcessor
#from document.service import DocumentServiceV1, Document
from rag.sql.postgres_db_loader import get_postgres_engine
from rag.vectordb.postgres_handler import PostgresHandler
from rag.vectordb.postgres_node_storage import PostgresNodeStorage
from datetime import datetime
import pandas as pd
import os

# WILL DELETE LATER
class Document:
    def __init__(self, id, title, type, object_name, created_at, updated_at):
        self.id = id
        self.title = title
        self.type = type
        self.object_name = object_name
        self.created_at = created_at
        self.updated_at = updated_at

    def generate_presigned_url(self) -> str:
        # Placeholder method to generate a presigned URL
        return '' # Example implementation

# WILL DELETE LATER
class DocumentServiceV1:

    def get_documents(self, filter) -> list:

        return []
    
class DocumentIndexing:
    def __init__(self):
        self.service = DocumentServiceV1()

    def fetch_documents(self, start_date: datetime = None):
        filter = {
            "created_after": start_date.isoformat(),
            "created_before": datetime.now().isoformat()
        }
        return self.service.get_documents(filter=filter)

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
            'title': document.title,
            'type': document.type,
            'object_name': document.object_name,
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
                self._store_tabular(document.title, data, summary)

            else:
                nodes = processor.process()
                nodes = [self._update_metadata(node, document) for node in nodes]
                self._store_vector(nodes)

    def _store_tabular(self, table_name: str, data: pd.DataFrame, summary: str):
        pass

    def _store_vector(self, nodes):
        pass