from rag.parsing.parsing_csv import CSVProcessor
from rag.parsing.parsing_txt import TXTProcessor
from rag.parsing.parsing_pdf import PDFProcessor
from rag.sql.postgres_db_loader import get_postgres_engine
from rag.vectordb.postgres_handler import PostgresHandler
from rag.vectordb.postgres_node_storage import PostgresNodeStorage
from document.document import Document
from document.service import DocumentServiceV1
from document.utils import generate_presigned_url
from document.dto import AWSConfig
import boto3
from sqlalchemy import text
from datetime import datetime
import pandas as pd
import requests
import os
    
class DocumentIndexing:
    def __init__(self, aws_config: AWSConfig, service:DocumentServiceV1):

        self.service = service
        self.aws_config = aws_config
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.aws_config.aws_access_key_id,
            aws_secret_access_key=self.aws_config.aws_secret_access_key,
            region_name=self.aws_config.aws_region,
            endpoint_url=self.aws_config.aws_endpoint_url
        )

    def fetch_documents(self, start_date: datetime = None) -> list:
        doc_filter = {
            "created_after": start_date.isoformat() if start_date else None,
            "created_before": datetime.now().isoformat()
        }
        doc_filter = {key: value for key, value in doc_filter.items() if value is not None}
        return self.service.get_documents(filter=doc_filter)

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

    def process_documents(self, start_date: datetime = None):
        """Main method to process documents based on their type."""
        documents = self.fetch_documents(start_date)
        
        for document in documents:

            document_url = generate_presigned_url(document, self.s3_client, self.aws_config.aws_public_bucket_name)

            # Ambil dokumen url
            response = requests.get(document_url)
            response.raise_for_status()

            document_path = f"temp.{document.type}"
            with open(document_path, "wb") as file:
                file.write(response.content)

            processor = self._get_processor(document.type, document_path)
            
            if document.type == 'csv':
                summary = processor.process()
                data = processor.df
                self._store_tabular(document.title, data, document, summary)

            else:
                nodes = processor.process()
                nodes = [self._update_metadata(node, document) for node in nodes]

                print(len(nodes))

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