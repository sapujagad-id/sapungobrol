from datetime import datetime
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4
import pytest
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from auth.controller import AuthControllerV1
from auth.dto import ProfileResponse
from document.controller import DocumentControllerV1
from document.document import DocumentType
from document.dto import DocumentCreate, DocumentFilter
from document.repository import DocumentModel, PostgresDocumentRepository
from document.service import DocumentServiceV1
from document.view import DocumentViewV1

@pytest.fixture
def setup_session():
    # Set up an in-memory SQLite session for testing
    engine = create_engine("sqlite:///:memory:")
    session = sessionmaker(bind=engine)
    DocumentModel.metadata.create_all(engine)
    return session

@pytest.fixture
def setup_repository(setup_session):
    return PostgresDocumentRepository(setup_session)
  
@pytest.fixture()
@patch("boto3.client")
def setup_service(mock_boto_client, setup_repository):
    """Set up DocumentServiceV1 with mocked dependencies."""
    mock_s3_client = MagicMock()
    mock_boto_client.return_value = mock_s3_client
    
    service = DocumentServiceV1(
        aws_access_key_id="test_access_key",
        aws_secret_access_key="test_secret_key",
        bucket_name="test_bucket",
        aws_region_name="ap-southeast-3",
        repository=setup_repository
    )
    
    # Pass back the mock S3 client for verification in tests
    service.mock_s3_client = mock_s3_client
    return service

@pytest.fixture
def setup_controller(setup_service):
    return DocumentControllerV1(service=setup_service)

@pytest.fixture()
def setup_view(setup_service):
    """Setup the BotViewV1 with mocked controller and service."""
    mock_controller = Mock(spec=AuthControllerV1)
    view = DocumentViewV1(setup_service, mock_controller)
    view.auth_controller = mock_controller
    return view

@pytest.fixture
def setup_documents(setup_repository):
    # Add some documents to the test database (side-effect)
    documents = [
        DocumentCreate(
            title="Document 1",
            type=DocumentType.CSV,
            object_name="doc1.csv",
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        DocumentCreate(
            title="Document 2",
            type=DocumentType.PDF,
            object_name="doc2.pdf",
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
    ]
    for doc in documents:
      setup_repository.create_document(doc_create=doc)
    return setup_repository.get_documents(DocumentFilter())

@pytest.fixture()
def dummy_user_profile():
    """Return a mock user profile."""
    return ProfileResponse(data={
        "id": str(uuid4()),  # Replace with actual fields expected by User
        "email": "test@broom.id",
        "created_at": "2024-10-24T00:00:00Z",
        # Include other necessary fields...
    })

@pytest.fixture()
def setup_jwt_secret():
    """Set up a mock JWT secret."""
    return "some_arbitrary_secret_here"