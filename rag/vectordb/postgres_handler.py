import os
from typing import Any, Dict, List

import openai
import psycopg2


class PostgresHandler:
    """Handles interactions with PostgreSQL (pgvector), including multi-table access for hierarchical access levels."""

    def __init__(self, db_name: str, user: str, password: str, host: str, port: int, dimension: int):
        self.db_name = db_name
        self.user = user
        self.password = password
        self.host = host
        self.port = port
        self.dimension = dimension
        self.total_access_levels = int(os.getenv("TOTAL_ACCESS_LEVELS"))
        
        # Initialize the connection
        self.conn = psycopg2.connect(
            dbname=self.db_name,
            user=self.user,
            password=self.password,
            host=self.host,
            port=self.port
        )
        self.cursor = self.conn.cursor()
        
        # Ensure pgvector extension is available
        self._initialize_pgvector_extension()
        
        # Pre-create tables for each access level
        self._initialize_tables()

    def _initialize_pgvector_extension(self):
        """Creates pgvector extension if it does not exist."""
        self.cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        self.conn.commit()

    def _initialize_tables(self):
        """Creates tables for each access level if they do not exist."""
        for level in range(1, self.total_access_levels + 1):
            table_name = f"index_L{level}"
            create_table_query = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id SERIAL PRIMARY KEY,
                item_id TEXT UNIQUE,
                embedding VECTOR({self.dimension})
            );
            """
            self.cursor.execute(create_table_query)
        self.conn.commit()

    def upsert_vectors(self, vectors: List[Dict[str, Any]], level: int):
        """Inserts vectors into the PostgreSQL table for the given level and duplicates them in higher levels."""
        for lvl in range(level, self.total_access_levels + 1):  # Start from the specified level up to the highest level
            table_name = f"index_L{lvl}"
            for vector in vectors:
                item_id = vector['id']
                embedding = vector['values']
                self.cursor.execute(
                    f"INSERT INTO {table_name} (item_id, embedding) VALUES (%s, %s) "
                    f"ON CONFLICT (item_id) DO UPDATE SET embedding = EXCLUDED.embedding;",
                    (item_id, embedding)
                )
        self.conn.commit()

    def query(self, vector, access_level: int, top_k: int = 10):
        """Queries only the table corresponding to the specified access level using cosine similarity."""
        table_name = f"index_L{access_level}"
        self.cursor.execute(
            f"""
            SELECT item_id, embedding <-> %s::vector AS distance
            FROM {table_name}
            ORDER BY distance
            LIMIT %s;
            """,
            (vector, top_k)
        )
        return self.cursor.fetchall()

    def close(self):
        """Closes the database connection."""
        self.cursor.close()
        self.conn.close()


if __name__ == "__main__":  # pragma: no cover
    POSTGRES_DB = os.getenv("POSTGRES_DB")
    POSTGRES_USER = os.getenv("POSTGRES_USER")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
    POSTGRES_HOST = os.getenv("POSTGRES_HOST")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    if not (POSTGRES_DB and POSTGRES_USER and POSTGRES_PASSWORD and OPENAI_API_KEY):
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

    # Get access level and query input from the user
    access_level = int(input(f"Enter your access level (1 to {postgres_handler.total_access_levels}): "))
    query_text = input("Enter your query: ")
    
    embedding_result = openai.embeddings.create(
        input=query_text,
        model="text-embedding-3-small"
    )
    query_vector = embedding_result.data[0].embedding
    
    # Perform the query
    top_k = 5
    query_results = postgres_handler.query(query_vector, access_level=access_level, top_k=top_k)
    
    print(f"Top {top_k} most relevant results:")
    for result in query_results:
        print(result)
    
    postgres_handler.close()