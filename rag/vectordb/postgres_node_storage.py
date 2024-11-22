from typing import List
from rag.vectordb.postgres_handler import PostgresHandler
from rag.parsing.parsing_pdf import PDFProcessor
from rag.parsing.parsing_txt import TXTProcessor
import openai
import os

class PostgresNodeStorage:
    """Orchestrates the storage of document nodes into PostgreSQL (pgvector) via embedding vectors."""

    def __init__(self, postgres_handler: PostgresHandler):
        self.postgres_handler = postgres_handler

    def _embed_node(self, node_text: str):
        """Converts node text into a vector using OpenAI's text-embedding-3-small model."""
        response = openai.embeddings.create(
            input=node_text,
            model="text-embedding-3-small"
        )
        return response.data[0].embedding

    def store_nodes(self, nodes: List[str], access_level: int):
        """Stores the nodes as vectors in PostgreSQL for the given access level and duplicates them in higher levels."""
        vectors = []
        for i, node in enumerate(nodes):
            vector = self._embed_node(node)
            vectors.append({
                "id": str(i), 
                "values": vector, 
                "text_content": node
            })
            
        if not vectors:
            raise ValueError("No vectors to store.")

        # Store vectors in tables for the given access level and higher levels
        self.postgres_handler.upsert_vectors(vectors, access_level)

if __name__ == "__main__":  # pragma: no cover
    POSTGRES_DB = os.getenv("POSTGRES_DB")
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    ACCESS_LEVEL = 3
    DOCUMENT_PATH = "C:/Users/arkan/Downloads/University/ppl/sapungobrol/data/image-based-pdf-sample.pdf"
    
    if not POSTGRES_DB or not POSTGRES_USER or not POSTGRES_PASSWORD or not OPENAI_API_KEY:
        raise EnvironmentError("PostgreSQL and OpenAI credentials must be set.")

    openai.api_key = OPENAI_API_KEY

    postgres_handler = PostgresHandler(
        db_name=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dimension=1536
    )

    processor = PDFProcessor(DOCUMENT_PATH)
    nodes = processor.process()
    
    print(nodes)
    
    postgres_storage = PostgresNodeStorage(postgres_handler)
    postgres_storage.store_nodes([node.text for node in nodes], ACCESS_LEVEL)

    print(f"Stored {len(nodes)} nodes in PostgreSQL up to level {ACCESS_LEVEL}!")
    postgres_handler.close()
