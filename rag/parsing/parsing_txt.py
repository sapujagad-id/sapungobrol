from rag.parsing.processor import FileProcessor
from llama_index.core import SimpleDirectoryReader
from pathlib import Path
from llama_index.core.node_parser import SentenceSplitter

class TXTProcessor(FileProcessor):
    
    def __init__(self, document_path: str, chunk_size: int = 200, chunk_overlap: int = 0):
        self.document_path = Path(document_path)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.splitting_parser = SentenceSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)

    def _load_document(self):
        try:
            return SimpleDirectoryReader(input_files=[self.document_path]).load_data()
        except Exception as e:
            raise RuntimeError(f"Failed to load document: {str(e)}")

    def get_nodes(self, documents):
        try:
            return self.splitting_parser.get_nodes_from_documents(documents=documents)
        except Exception as e:
            raise RuntimeError(f"Failed to get nodes from documents: {str(e)}")

    def process(self):
        documents = self._load_document()
        return self.get_nodes(documents)

if __name__=="__main__":
    processor_txt = TXTProcessor(document_path='/Users/nyoosteven/Kuliah/PPL/sapungobrol/data/ppl_faq (1).txt')
    nodes = processor_txt.process()