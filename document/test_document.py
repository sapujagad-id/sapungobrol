from pydantic import ValidationError
import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import Mock, patch
from document import Document, DocumentTitleError, DocumentType, DocumentTypeError, ObjectNameError, DocumentPresignedURLError
from botocore.exceptions import ClientError

# Helper to create a valid document
def create_valid_document():
    return Document(
        id=uuid4(),
        type=DocumentType.CSV,
        title="Sample Document",
        object_name="sample.csv",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
class TestDocument:
    # Test for successful document creation with valid data
    def test_document_creation(self):
        doc = create_valid_document()
        doc.validate()
        assert doc.type == DocumentType.CSV
        assert doc.title == "Sample Document"
        assert doc.object_name == "sample.csv"
        assert isinstance(doc.id, uuid4().__class__)  # Check if id is UUID4

    # Test for invalid type error
    def test_invalid_document_type(self):
        with pytest.raises(DocumentTypeError) as excinfo:
            doc = create_valid_document()
            doc.type = "invalid_type"  # Directly assign an invalid type
            doc.validate()
        assert str(excinfo.value) == "Data Source Type is not valid"

    # Test for missing title
    def test_missing_document_title(self):
        with pytest.raises(DocumentTitleError) as excinfo:
            doc = create_valid_document()
            doc.title = ""  # Clear title to trigger error
            doc.validate()
        assert str(excinfo.value) == "Document title is required"

    # Test for missing object name
    def test_missing_object_name(self):
        with pytest.raises(ObjectNameError) as excinfo:
            doc = create_valid_document()
            doc.object_name = ""  # Clear object_name to trigger error
            doc.validate()
        assert str(excinfo.value) == "Object name is required"

    # Test for all required fields missing - using Pydantic's ValidationError
    def test_document_validation_errors(self):
        with pytest.raises(ValidationError) as excinfo:
            Document(
                id=None,  # Missing UUID
                type=None,  # Missing type
                title=None,  # Missing title
                object_name=None,  # Missing object_name
                created_at=None,
                updated_at=None
            )
        assert len(excinfo.value.errors()) > 0  # Multiple validation errors raised

    @patch("boto3.client")
    def test_generate_presigned_url_success(self, mock_s3_client):
        # Arrange
        document = create_valid_document()
        document.object_name = "sample.csv"
        presigned_url = "https://example.com/sample.csv?X-Amz-Security-Token=..."
        
        # Mock S3 client response for generate_presigned_url
        mock_s3_client.return_value.generate_presigned_url.return_value = presigned_url
        
        # Act
        response = document.generate_presigned_url(mock_s3_client.return_value, "test-bucket")

        # Assert
        assert response == presigned_url
        mock_s3_client.return_value.generate_presigned_url.assert_called_once_with(
            'get_object',
            Params={'Bucket': "test-bucket", 'Key': "sample.csv"},
            ExpiresIn=28800
        )

    @patch("boto3.client")
    def test_generate_presigned_url_failure(self, mock_s3_client):
        # Arrange
        document = create_valid_document()
        document.object_name = "sample.csv"
        
        # Simulate a ClientError when generate_presigned_url is called
        mock_s3_client.return_value.generate_presigned_url.side_effect = ClientError(
            error_response={"Error": {"Code": "403", "Message": "Forbidden"}},
            operation_name="generate_presigned_url"
        )
        
        # Act & Assert
        with pytest.raises(DocumentPresignedURLError):
            document.generate_presigned_url(mock_s3_client.return_value, "test-bucket")