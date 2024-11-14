from rag.vectordb.postgres_handler import PostgresHandler
import openai

class Retriever:
    def __init__(self, postgres_handler: PostgresHandler):
        self.postgres_handler = postgres_handler

    def _retrieve_context_vector(self, query, access_level, top_k=5) -> list:
        embedding_result = openai.embeddings.create(
            input=query,
            model="text-embedding-3-small"
        )
        query_vector = embedding_result.data[0].embedding
        
        return self.postgres_handler.query(query_vector, access_level=access_level, top_k=top_k)

    def _retrieve_context_tabular(self, query, access_level) -> str:
        del query, access_level
        return ''

    def query(self, query, access_level, top_k=5):
        # Retrieve Nodes based on the vector
        context_vector = self._retrieve_context_vector(query, access_level, top_k)

        # Retrieve tabular context
        context_tabular = self._retrieve_context_tabular(query, access_level)

        # Create the final context
        final_context = context_vector.copy()
        final_context.append(context_tabular)

        return final_context
