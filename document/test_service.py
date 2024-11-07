from datetime import datetime
from uuid import uuid4
import pytest
from sqlalchemy import create_engine
from document.document import DocumentType, ObjectNameError
from document.dto import DocumentCreate, DocumentFilter
from document.repository import DocumentModel, PostgresDocumentRepository
from document.service import DocumentServiceV1

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
    return documents

# Test cases for DocumentServiceV1 methods
def test_get_documents(setup_service, setup_documents):
    filter_data = DocumentFilter(created_after="2000-01-01")
    documents = setup_service.get_documents(filter_data)
    assert documents is not None
    assert len(documents) == len(setup_documents)

def test_get_document_by_name(setup_service, setup_documents):
    document = setup_service.get_document_by_name("doc1.csv")
    assert document is not None
    assert document.object_name == "doc1.csv"
    assert document.title == "Document 1"

def test_get_document_by_name_not_found(setup_service):
    document = setup_service.get_document_by_name("nonexistent.csv")
    assert document is None

def test_create_document_successful(setup_service, setup_repository):
    new_document = DocumentCreate(
        type=DocumentType.TXT,
        title="New Document",
        object_name="new_doc.txt",
    )
    setup_service.create_document(new_document)
    document = setup_repository.get_documents(DocumentFilter(object_name="new_doc.txt"))
    assert len(document) == 1
    assert document[0].title == "New Document"

def test_create_document_existing_name_raises_error(setup_service):
    existing_document = DocumentCreate(
        type=DocumentType.CSV,
        title="Real Document",
        object_name="doc1.csv",
    )
    setup_service.create_document(existing_document)
    existing_document.title = "Duplicate Document"
    with pytest.raises(ObjectNameError):
        setup_service.create_document(existing_document)
