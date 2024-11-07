from datetime import datetime
from uuid import uuid4
from document.document import DocumentType
from document.dto import DocumentCreate, DocumentFilter
from document.repository import DocumentModel, PostgresDocumentRepository, DocumentRepository
from loguru import logger


def test_create_document(setup_repository, setup_session):
    doc_create = DocumentCreate(
        type=DocumentType.CSV.value,
        title="Sample Document",
        object_name="sample_object",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    setup_repository.create_document(doc_create)
    
    # verify document exists
    with setup_session() as session:
        result = session.query(DocumentModel).filter_by(object_name="sample_object").first()
        assert result is not None
        assert result.title == "Sample Document"
        assert result.type == DocumentType.CSV.value


def test_get_document_by_id(setup_repository, setup_session):
    doc_id = uuid4()
    document = DocumentModel(
        id=doc_id,
        type=DocumentType.PDF.value,
        title="PDF Document",
        object_name="pdf_object",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    with setup_session() as session:
        session.add(document)
        session.commit()

    result = setup_repository.get_document_by_id(doc_id)
    assert result is not None
    assert result.title == "PDF Document"
    assert result.object_name == "pdf_object"


def test_get_document_by_name(setup_repository, setup_session):
    document = DocumentModel(
        id=uuid4(),
        type=DocumentType.TXT.value,
        title="Text Document",
        object_name="text_object",
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    with setup_session() as session:
        session.add(document)
        session.commit()

    result = setup_repository.get_document_by_name("text_object")
    assert result is not None
    assert result.title == "Text Document"
    assert result.type == DocumentType.TXT.value


def test_get_documents_with_filters(setup_repository, setup_session):
    documents = [
        DocumentModel(
            id=uuid4(),
            type=DocumentType.CSV.value,
            title="CSV Document",
            object_name="csv_object",
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        DocumentModel(
            id=uuid4(),
            type=DocumentType.PDF.value,
            title="PDF Document",
            object_name="pdf_object",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]
    with setup_session() as session:
        session.bulk_save_objects(documents)
        session.commit()

    # Filter to fetch only the PDF document
    filter = DocumentFilter(object_name="pdf_object", title="PDF Document", created_before=datetime.now())
    result = setup_repository.get_documents(filter)
    assert len(result) == 1
    assert result[0].title == "PDF Document"
    assert result[0].object_name == "pdf_object"
    
def test_get_documents_without_filters(setup_repository, setup_session):
    # Insert multiple documents
    documents = [
        DocumentModel(
            id=uuid4(),
            type=DocumentType.CSV.value,
            title="CSV Document",
            object_name="csv_object",
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        DocumentModel(
            id=uuid4(),
            type=DocumentType.PDF.value,
            title="PDF Document",
            object_name="pdf_object",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    ]
    with setup_session() as session:
        session.bulk_save_objects(documents)
        session.commit()

    result = setup_repository.get_documents(None)
    assert len(result) == 2


def test_get_documents_without_filters(setup_repository, setup_session):
    documents = [
        DocumentModel(
            id=uuid4(),
            type=DocumentType.CSV.value,
            title="CSV Document",
            object_name="csv_object"
        ),
        DocumentModel(
            id=uuid4(),
            type=DocumentType.PDF.value,
            title="PDF Document",
            object_name="pdf_object"
        )
    ]
    with setup_session() as session:
        session.bulk_save_objects(documents)
        session.commit()

    # Retrieve all documents without filters
    filter = DocumentFilter()
    result = setup_repository.get_documents(filter)
    assert len(result) == 2
