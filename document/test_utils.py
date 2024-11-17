import pytest
from unittest.mock import MagicMock
from document.utils import generate_presigned_url
from document.document import DocumentPresignedURLError

class TestGeneratePresignedURL:
    @pytest.fixture()
    def mock_s3_client(self, mock_boto_client):
        """Fixture to mock the S3 client"""
        mock_client = MagicMock()
        mock_client.generate_presigned_url.return_value = "http://mockurl.com"
        mock_boto_client.return_value = mock_client
        return mock_client

    
    def test_generate_presigned_url_success(self, mock_s3_client, setup_documents):
        """Test the happy path where URL is generated successfully"""
        # Use the first document from the setup_documents fixture
        doc_model = setup_documents[0]
        bucket_name = "mock-bucket"

        # Call the generate_presigned_url function
        url = generate_presigned_url(doc_model, mock_s3_client, bucket_name)

        # Assert the S3 client's generate_presigned_url method was called with the expected parameters
        mock_s3_client.generate_presigned_url.assert_called_once_with(
            'get_object',
            Params={'Bucket': bucket_name, 'Key': doc_model.object_name},
            ExpiresIn=28800
        )

        # Assert the generated URL is correct
        assert url == "http://mockurl.com"

    def test_generate_presigned_url_failure(self, mock_s3_client, setup_documents):
        """Test the failure path when presigned URL generation fails"""
        # Use the first document from the setup_documents fixture
        doc_model = setup_documents[0]
        bucket_name = "mock-bucket"

        # Simulate a failure in generating the presigned URL
        mock_s3_client.generate_presigned_url.side_effect = DocumentPresignedURLError

        # Call the generate_presigned_url function and assert that it raises the custom error
        with pytest.raises(DocumentPresignedURLError, match="Failed to generate presigned URL"):
            generate_presigned_url(doc_model, mock_s3_client, bucket_name)
