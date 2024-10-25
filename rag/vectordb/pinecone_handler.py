from pinecone import Pinecone
from pinecone import ServerlessSpec
import os
import openai

class PineconeHandler:
    """Handles all interactions with Pinecone, including indexing and querying."""

    def __init__(self, api_key: str, index_name: str, dimension: int, metric: str = "cosine", region: str = "us-east-1"):
        self.api_key = api_key
        self.index_name = index_name
        self.dimension = dimension
        self.metric = metric
        self.region = region
        self.index = self._initialize_index()

    def _initialize_index(self):
        """Initializes Pinecone connection and creates an index if it doesn't exist."""
        pc = Pinecone(api_key=self.api_key)
        
        # Check if the index already exists
        existing_indexes = [index['name'] for index in pc.list_indexes()]
        
        if self.index_name in existing_indexes:
            print(f"Index '{self.index_name}' already exists. Using existing index.")
        else:
            # Create the index only if it doesn't exist
            pc.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric=self.metric,
                spec=ServerlessSpec(
                  cloud="aws",
                  region=self.region
                )
            )
        
        return pc.Index(self.index_name)

    def upsert_vectors(self, vectors):
        """Upserts vectors into the Pinecone index."""
        self.index.upsert(vectors)

    def query(self, vector, top_k: int = 10):
        """Queries the Pinecone index and returns the top_k results."""
        return self.index.query(vector=vector, top_k=top_k)

if __name__ == "__main__":  # pragma: no cover
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    DOCUMENT_PATH = "data/ppl_testing_pdf.pdf"
    INDEX_NAME = "broom"

    pinecone_handler = PineconeHandler(api_key=PINECONE_API_KEY, index_name=INDEX_NAME, dimension=1536)

    query = input(f"Enter a query: ")
    
    embedding_result = openai.embeddings.create(
        input=query,
        model="text-embedding-3-small"
    )
    
    query_results = pinecone_handler.query(embedding_result.data[0].embedding, top_k=5)

    print(f"Top 5 most relevant results: {query_results}")