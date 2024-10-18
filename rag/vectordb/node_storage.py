from typing import List
from rag.vectordb.pinecone_handler import PineconeHandler
import openai

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


