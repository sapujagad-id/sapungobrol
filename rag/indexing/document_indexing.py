from rag.parsing.parsing_csv import CSVProcessor
from rag.parsing.parsing_txt import TXTProcessor
from rag.parsing.parsing_pdf import PDFProcessor
#from document.service import DocumentService
from datetime import datetime
import pandas as pd

# Will delete later
class Document:

    def __init__(self, id, name, type, object_url, created_at, updated_at):
        self.id = id
        self.name = name
        self.type = type
        self.object_url = object_url
        self.created_at = created_at
        self.updated_at = updated_at

    def generate_presigned_url(self) -> str:
        pass

class DocumentIndexing:
    def __init__(self):
        #self.service = DocumentService()
        #self.documents : list(Document)
        pass

    def _get_document_url(self, document: Document) -> str:
        document_url = document.generate_presigned_url()
        return document_url

    def fetch_documents(self) -> list[Document]:
        #documents = self.service.get_documents(filter:)
        return []
    
    def _update_metadata(node, document: Document):
        
        node.metadata['id'] = document.id
        node.metadata['name'] = document.name
        node.metadata['type'] = document.type
        node.metadata['object_url'] = document.object_url
        node.metadata['created_at'] = document.created_at
        node.metadata['updated_at'] = document.updated_at

        return node
    
    def documents_process(self):

        documents = self.fetch_documents()
        for document in documents:
            document_url = self._get_document_url(document)
            
            if document.type == 'csv':
                processor = CSVProcessor(document_url)
                summary = processor.process()
                data = processor.df
                self._store_tabular(data, summary)

            elif document.type == 'pdf':
                processor = PDFProcessor(document_url)
                nodes = processor.process()
                self._store_tabular(data, summary)

            elif document.type == 'txt':
                processor = TXTProcessor(document_url)
                nodes = processor.process()

            if document.type == 'pdf' or document.type == 'txt':
                for node in nodes:
                    node = self._update_metadata(node, document)
                self._store_vector(nodes)

    def _store_tabular(self, data: pd.DataFrame, summary: str):
        pass

    def _store_vector(self, nodes):
        pass