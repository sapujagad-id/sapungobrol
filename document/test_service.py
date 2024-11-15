from datetime import datetime
from uuid import uuid4
import pytest
from sqlalchemy import create_engine
from document.document import DocumentType, ObjectNameError
from document.dto import DocumentCreate, DocumentFilter
from document.repository import DocumentModel, PostgresDocumentRepository
from document.service import DocumentServiceV1
import io
from unittest.mock import ANY, MagicMock
import pytest
from botocore.exceptions import NoCredentialsError, PartialCredentialsError, BotoCoreError # type: ignore

class TestDocumentService:
    def test_get_documents(self, setup_service, setup_documents):
        filter_data = DocumentFilter(created_after="2000-01-01")
        documents = setup_service.get_documents(filter_data)
        assert documents is not None
        assert len(documents) == len(setup_documents)

    def test_get_document_by_name(self, setup_service, setup_documents):
        document = setup_service.get_document_by_name("doc1.csv")
        assert document is not None
        assert document.object_name == "doc1.csv"
        assert document.title == "Document 1"

    def test_get_document_by_name_not_found(self, setup_service):
        document = setup_service.get_document_by_name("nonexistent.csv")
        assert document is None

    def test_create_document_successful(self, setup_service, setup_repository):
        new_document = DocumentCreate(
            type=DocumentType.TXT,
            title="New Document",
            object_name="new_doc.txt",
            access_level=0,
        )
        setup_service.create_document(new_document)
        document = setup_repository.get_documents(DocumentFilter(object_name="new_doc.txt"))
        assert len(document) == 1
        assert document[0].title == "New Document"

    def test_create_document_existing_name_raises_error(self, setup_service):
        existing_document = DocumentCreate(
            type=DocumentType.CSV,
            title="Real Document",
            object_name="doc1.csv",
            access_level=0,
        )
        setup_service.create_document(existing_document)
        existing_document.title = "Duplicate Document"
        with pytest.raises(ObjectNameError):
            setup_service.create_document(existing_document)


    def test_upload_document_success(self, setup_service):
        # Prepare a mock file content for upload
        mock_file_content = MagicMock()
        mock_file_content.file = io.BytesIO(b"test data")

        # Call the upload_document method
        setup_service.upload_document(mock_file_content, "test_object_name")

        # Assert that the S3 upload_fileobj method was called once
        setup_service.mock_s3_client.upload_fileobj.assert_called_once_with(
            ANY, "test_bucket", "test_object_name"
        )


    def test_upload_document_no_credentials_error(self, setup_service):
        # Simulate NoCredentialsError
        setup_service.mock_s3_client.upload_fileobj.side_effect = NoCredentialsError

        mock_file_content = MagicMock()
        mock_file_content.file.read.return_value = b"test data"

        with pytest.raises(NoCredentialsError):
            setup_service.upload_document(mock_file_content, "test_object_name")

    def test_upload_document_partial_credentials_error(self, setup_service):
        # Simulate PartialCredentialsError
        setup_service.mock_s3_client.upload_fileobj.side_effect = PartialCredentialsError(
        provider='aws', cred_var='aws_secret_access_key'
        )

        mock_file_content = MagicMock()
        mock_file_content.file = io.BytesIO(b"test data")

        with pytest.raises(PartialCredentialsError):
            setup_service.upload_document(mock_file_content, "test_object_name")

    def test_upload_document_botocore_error(self, setup_service):
        # Simulate a generic BotoCoreError
        setup_service.mock_s3_client.upload_fileobj.side_effect = BotoCoreError

        mock_file_content = MagicMock()
        mock_file_content.file.read.return_value = b"test data"

        with pytest.raises(BotoCoreError):
            setup_service.upload_document(mock_file_content, "test_object_name")
