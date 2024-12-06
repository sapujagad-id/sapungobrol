from pathlib import Path

import easyocr
import numpy as np
from llama_index.core import Document
from llama_index.core.node_parser import SentenceSplitter
from llama_index.readers.file.docs.base import PDFReader
from pdf2image import convert_from_path

from rag.parsing.processor import FileProcessor


class PDFProcessor(FileProcessor):
    
    def __init__(self, document_path: str, chunk_size: int = 200, chunk_overlap: int = 0):
        self.document_path = Path(document_path)
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.pdf_reader = PDFReader(return_full_document=True)
        self.splitting_parser = SentenceSplitter(chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap)
        self.ocr_reader = easyocr.Reader(['en'], gpu=False)

    def _extract_text_with_ocr(self):
        text_data = []
        try:
            pages = convert_from_path(self.document_path)
            for page_number, page_image in enumerate(pages):
                page_image_array = np.array(page_image)
                text = self.ocr_reader.readtext(page_image_array, detail=0)
                text_data.append(f"Page {page_number + 1} OCR Text:\n{text}")
            return "\n".join(text_data)
        except Exception as e:
            raise RuntimeError(f"Failed to perform OCR on document: {str(e)}")

    
    def _load_document(self):
        full_text = []
        try:
            documents = self.pdf_reader.load_data(file=self.document_path)
            if documents and isinstance(documents, list) and 'text' in documents[0]:
                extracted_text = documents[0]['text']
                full_text.append(f"Extracted Text:\n{extracted_text}")
        except Exception as e:
            raise RuntimeError(f"Failed to load document: {str(e)}")
        
        try:
            ocr_text = self._extract_text_with_ocr()
            full_text.append(f"OCR Text:\n{ocr_text}")
        except Exception as e:
            raise RuntimeError(f"Failed to load document: {str(e)}")
        
        combined_text = "\n\n".join(full_text)
        return [Document(text=combined_text, id_=self.document_path.name)]

    def get_nodes(self, documents):
        try:
            return self.splitting_parser.get_nodes_from_documents(documents=documents)
        except Exception as e:
            raise RuntimeError(f"Failed to get nodes from documents: {str(e)}")

    def process(self):
        documents = self._load_document()
        return self.get_nodes(documents)