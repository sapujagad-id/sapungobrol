from rag.parsing.processor import FileProcessor
from llama_index.readers.file.docs.base import PDFReader
from pathlib import Path
from llama_index.core.node_parser import SentenceSplitter

class PDFProcessor(FileProcessor):
    
    def __init__(self, document_path: str, chunk_size: int = 200, chunk_overlap: int = 0):
        self.document_path = Path(document_path)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.pdf_reader = PDFReader(return_full_document=True)
        self.splitting_parser = SentenceSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)

    def load_document(self):
        return self.pdf_reader.load_data(file=self.document_path)

    def get_nodes(self, documents):
        return self.splitting_parser.get_nodes_from_documents(documents=documents)

    def process(self):
        documents = self.load_document()
        return self.get_nodes(documents)

# if __name__=="__main__":
#     processor = PDFProcessor("data/ppl_testing_pdf.pdf")
#     nodes = processor.process()
#     print(len(nodes))
