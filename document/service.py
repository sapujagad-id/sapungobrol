import io
from abc import ABC, abstractmethod

import boto3
from botocore.exceptions import (BotoCoreError, NoCredentialsError,
                                 PartialCredentialsError)
from loguru import logger

from document.document import ObjectNameError
from document.dto import (AWSConfig, DocumentCreate, DocumentFilter,
                          DocumentResponse)
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
    def __init__(self, aws_config: AWSConfig, repository: DocumentRepository):
        super().__init__()
        self.repository = repository
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_config.aws_access_key_id,
            aws_secret_access_key=aws_config.aws_secret_access_key,
            region_name=aws_config.aws_region,
            endpoint_url=aws_config.aws_endpoint_url
        )
        self.bucket_name = aws_config.aws_public_bucket_name
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
        self.logger.debug(f"model dump: {request.model_dump()}" )
        if self.repository.get_document_by_name(request.object_name) is None:
            self.repository.create_document(request)
        else:
            raise ObjectNameError("Object by this name already exists")