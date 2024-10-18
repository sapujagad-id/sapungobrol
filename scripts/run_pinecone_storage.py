# run with python -m scripts.run_pinecone_storage
import os
from rag.vectordb.pinecone_handler import PineconeHandler
from rag.vectordb.node_storage import PineconeNodeStorage
from rag.parsing.parsing_pdf import PDFProcessor
import openai

if __name__ == "__main__":
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DOCUMENT_PATH = "data/ppl_testing_pdf.pdf"
    INDEX_NAME = "broom"
    
    
    if not PINECONE_API_KEY or not OPENAI_API_KEY:
        raise EnvironmentError("PINECONE_API_KEY and OPENAI_API_KEY must be set.")

    openai.api_key = OPENAI_API_KEY

    pinecone_handler = PineconeHandler(
        api_key=PINECONE_API_KEY,
        index_name=INDEX_NAME,
        dimension=1536
    )

    processor = PDFProcessor(DOCUMENT_PATH)
    nodes = processor.process()

    pinecone_storage = PineconeNodeStorage(pinecone_handler)

    pinecone_storage.store_nodes([node.text for node in nodes])

    print(f"Stored {len(nodes)} nodes in Pinecone!")