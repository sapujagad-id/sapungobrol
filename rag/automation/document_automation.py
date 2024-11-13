from rag.parsing.parsing_csv import CSVProcessor
from rag.parsing.parsing_txt import TXTProcessor
from rag.parsing.parsing_pdf import PDFProcessor
from rag.sql.postgres_db_loader import get_postgres_engine
from rag.vectordb.postgres_handler import PostgresHandler
from rag.vectordb.postgres_node_storage import PostgresNodeStorage
from document.document import Document
from document.service import DocumentServiceV1
from sqlalchemy import text
from datetime import datetime
import pandas as pd
import os
    
class DocumentIndexing:
    def __init__(self, service: DocumentServiceV1):
        self.service = service

    def fetch_documents(self, start_date: datetime = None):
        doc_filter = {
            "created_after": start_date.isoformat(),
            "created_before": datetime.now().isoformat()
        }
        return self.service.get_documents(doc_filter=doc_filter)

    def _get_processor(self, document_type: str, document_url: str):
        """Returns the appropriate processor based on document type."""
        processors = {
            'csv': CSVProcessor,
            'pdf': PDFProcessor,
            'txt': TXTProcessor,
        }
        processor_class = processors.get(document_type)
        if processor_class:
            return processor_class(document_url)
        raise ValueError(f"Unsupported document type: {document_type}")

    def _update_metadata(self, node, document: Document):
        """Updates metadata of a node based on document properties."""
        node.metadata.update({
            'id': document.id,
            'title': document.title,
            'type': document.type,
            'object_name': document.object_name,
            'created_at': document.created_at,
            'updated_at': document.updated_at,
            'access_level': document.access_level
        })
        return node

    def process_documents(self):
        """Main method to process documents based on their type."""
        documents = self.fetch_documents()
        
        for document in documents:
            document_url = document.generate_presigned_url()
            processor = self._get_processor(document.type, document_url)
            
            if document.type == 'csv':
                summary = processor.process()
                data = processor.df
                self._store_tabular(document.title, data, document, summary)

            else:
                nodes = processor.process()
                nodes = [self._update_metadata(node, document) for node in nodes]
                self._store_vector(nodes, document.access_level)

    def _store_tabular(self, table_name: str, data: pd.DataFrame, document: Document, summary: str):
        engine = get_postgres_engine()

        data["access_level"] = document.access_level

        data.to_sql(table_name, con=engine, if_exists="replace", index=False)
        
        create_metadata_table_query = text(
            "CREATE TABLE IF NOT EXISTS metadata_table (\n"
            "    id SERIAL PRIMARY KEY,\n"
            "    document_id VARCHAR NOT NULL,\n"
            "    title VARCHAR,\n"
            "    type VARCHAR,\n"
            "    object_name VARCHAR,\n"
            "    created_at TIMESTAMP,\n"
            "    updated_at TIMESTAMP,\n"
            "    access_level INTEGER,\n"
            "    summary TEXT\n"
            ");"
        )
        
        with engine.connect() as conn:
            conn.execute(create_metadata_table_query)

            insert_metadata_query = text(
                "INSERT INTO metadata_table (document_id, title, type, object_name, created_at, updated_at, access_level, summary)\n"
                "VALUES (:document_id, :title, :type, :object_name, :created_at, :updated_at, :access_level, :summary)\n"
                "ON CONFLICT (document_id) DO UPDATE\n"
                "SET title = EXCLUDED.title,\n"
                "    type = EXCLUDED.type,\n"
                "    object_name = EXCLUDED.object_name,\n"
                "    created_at = EXCLUDED.created_at,\n"
                "    updated_at = EXCLUDED.updated_at,\n"
                "    access_level = EXCLUDED.access_level,\n"
                "    summary = EXCLUDED.summary;"
            )

            conn.execute(insert_metadata_query, {
                "document_id": document.id,
                "title": document.title,
                "type": document.type,
                "object_name": document.object_name,
                "created_at": document.created_at,
                "updated_at": document.updated_at,
                "access_level": document.access_level,
                "summary": summary
            })

    def _store_vector(self, nodes, access_level):
        POSTGRES_DB = os.getenv("POSTGRES_DB")
        POSTGRES_USER = os.getenv("POSTGRES_USER")
        POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
        POSTGRES_HOST = os.getenv("POSTGRES_HOST")
        POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
        
        postgres_handler = PostgresHandler(
            db_name=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            dimension=1536
        )

        postgres_storage = PostgresNodeStorage(postgres_handler)
        postgres_storage.store_nodes([node.text for node in nodes], access_level)

        postgres_handler.close()
    