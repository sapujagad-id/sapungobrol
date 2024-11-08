from abc import ABC, abstractmethod
import io

from loguru import logger
import boto3
from botocore.exceptions import BotoCoreError, NoCredentialsError, PartialCredentialsError

from document.document import ObjectNameError
from document.dto import DocumentCreate, DocumentFilter, DocumentResponse, DocumentUpdate
from document.repository import DocumentRepository


class DocumentService(ABC):
    @abstractmethod
    def upload_document(self, file, object_name):
        pass

    @abstractmethod
    def get_documents(self, filter: DocumentFilter) -> list[DocumentResponse]:
        pass
      
    @abstractmethod
    def get_document_by_name(self, object_name: str) -> DocumentResponse:
        pass
      
    @abstractmethod
    def get_document_by_id(self, doc_id: str) -> DocumentResponse:
        pass

    @abstractmethod
    def create_document(self, request: DocumentCreate):
        pass

    # note: Not implemented to ensure vector database and document entries are not out of sync
    # @abstractmethod
    # def update_document(self, doc_id: str, request: DocumentUpdate):
    #     pass
    
    # @abstractmethod
    # def delete_document(self, doc_id: str):
    #     pass
      
class DocumentServiceV1(DocumentService):
    def __init__(self, aws_access_key_id, aws_secret_access_key, bucket_name, aws_region_name, repository: DocumentRepository):
        super().__init__()
        self.repository = repository
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=aws_region_name,
            endpoint_url="https://broom-magang.s3.ap-southeast-3.amazonaws.com"
        )
        self.bucket_name = bucket_name
        self.logger = logger.bind(service="DocumentService")

    def upload_document(self, file_content, object_name):
        try:
            file_content_bytes = file_content.file.read()
            file_object = io.BytesIO(file_content_bytes)

            self.s3_client.upload_fileobj(file_object, self.bucket_name, object_name)
        except NoCredentialsError:
            self.logger.error("AWS credentials not found.")
            raise
        except PartialCredentialsError:
            self.logger.error("Incomplete AWS credentials.")
            raise
        except BotoCoreError as e:
            self.logger.error(f"Error uploading file to S3: {e}")
            raise
        
    def get_documents(self, filter: DocumentFilter) -> list[DocumentResponse] | None:
        docs = self.repository.get_documents(filter=filter)
        return docs if docs else None
      
    def get_document_by_name(self, object_name: str) -> DocumentResponse | None:
        doc = self.repository.get_document_by_name(object_name=object_name)
        return doc if doc else None
      
    def get_document_by_id(self, doc_id: str) -> DocumentResponse | None:
        doc = self.repository.get_document_by_id(doc_id=doc_id)
        return doc if doc else None

    def create_document(self, request: DocumentCreate):
        request.validate()
        print(request.model_dump())
        if self.repository.get_document_by_name(request.object_name) is None:
            self.repository.create_document(request)
        else:
            raise ObjectNameError