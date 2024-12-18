import os
from typing import List

import openai

from rag.parsing.parsing_txt import TXTProcessor
from rag.vectordb.pinecone.pinecone_handler import PineconeHandler


class PineconeNodeStorage:
    """Orchestrates the storage of document nodes into Pinecone via embedding vectors."""

    def __init__(self, pinecone_handler: PineconeHandler):
        self.pinecone_handler = pinecone_handler

    def _embed_node(self, node_text: str):
        """Converts node text into a vector using OpenAI's text-embedding-3-small model."""
        response = openai.embeddings.create(
            input=node_text,
            model="text-embedding-3-small"
        )
        
        return response.data[0].embedding

    def store_nodes(self, nodes: List[str]):
        """Stores the nodes as vectors in Pinecone."""
        vectors = []
        for i, node in enumerate(nodes):
            vector = self._embed_node(node)
            vectors.append({"id": str(i), "values": vector})
            
        if not vectors:
          raise ValueError("No vectors to store.")

        self.pinecone_handler.upsert_vectors(vectors)

if __name__ == "__main__":  # pragma: no cover
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    DOCUMENT_PATH = "C:/Users/arkan/Downloads/University/ppl/sapungobrol/data/ppl_faq (1).txt"
    INDEX_NAME = "broom"


    if not PINECONE_API_KEY or not OPENAI_API_KEY:
        raise EnvironmentError("PINECONE_API_KEY and OPENAI_API_KEY must be set.")

    openai.api_key = OPENAI_API_KEY

    pinecone_handler = PineconeHandler(
        api_key=PINECONE_API_KEY,
        index_name=INDEX_NAME,
        dimension=1536
    )

    processor = TXTProcessor(DOCUMENT_PATH)
    nodes = processor.process()

    pinecone_storage = PineconeNodeStorage(pinecone_handler)

    pinecone_storage.store_nodes([node.text for node in nodes])

    print(f"Stored {len(nodes)} nodes in Pinecone!")
