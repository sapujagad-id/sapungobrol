from datetime import datetime
import pytest
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from document.controller import DocumentControllerV1
from document.document import DocumentType
from document.dto import DocumentCreate, DocumentFilter
from document.repository import DocumentModel, PostgresDocumentRepository
from document.service import DocumentServiceV1

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
  
@pytest.fixture
def setup_service(setup_repository):
  return DocumentServiceV1(setup_repository)

@pytest.fixture
def setup_controller(setup_service):
    return DocumentControllerV1(service=setup_service)

@pytest.fixture
def setup_documents(setup_repository):
    # Add some documents to the test database
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