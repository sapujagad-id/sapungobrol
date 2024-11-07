from rag.parsing.processor import FileProcessor
from llama_index.readers.file.docs.base import PDFReader
from pathlib import Path
from llama_index.core.node_parser import SentenceSplitter

class PDFProcessor(FileProcessor):
    
    def __init__(self, chunk_size: int = 200, chunk_overlap: int = 0):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.pdf_reader = PDFReader(return_full_document=True)
        self.splitting_parser = SentenceSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)

    def _load_document(self):
        try:
            return self.pdf_reader.load_data(file=self.document_path)
        except Exception as e:
            raise RuntimeError(f"Failed to load document: {str(e)}")

    def get_nodes(self, documents):
        try:
            return self.splitting_parser.get_nodes_from_documents(documents=documents)
        except Exception as e:
            raise RuntimeError(f"Failed to get nodes from documents: {str(e)}")

    def process(self, document_path: str):
        self.document_path = document_path
        documents = self._load_document()
        return self.get_nodes(documents)