import pytest
from fastapi import HTTPException, UploadFile
from document.controller import DocumentControllerV1
from document.dto import DocumentCreate, DocumentFilter
from document.service import DocumentServiceV1
from document.document import DocumentTypeError, DocumentTitleError, ObjectNameError
from io import BytesIO


def test_fetch_documents_found(setup_controller, setup_documents):
    # Use filter that matches setup_documents fixture data
    documents = setup_controller.fetch_documents(object_name="doc1.csv")
    assert documents is not None
    assert len(documents) == 1
    assert documents[0].title == "Document 1"

def test_fetch_documents_not_found(setup_controller):
    res = setup_controller.fetch_documents(object_name="nonexistent.csv")
    assert res.status_code == 404

def test_fetch_document_by_name_found(setup_controller, setup_documents):
    document = setup_controller.fetch_document_by_name("doc1.csv")
    assert document is not None
    assert document.title == "Document 1"
    assert document.object_name == "doc1.csv"

def test_fetch_document_by_name_not_found(setup_controller):
    res = setup_controller.fetch_document_by_name("nonexistent.csv")
    assert res.status_code == 404

def test_fetch_document_by_id_found(setup_controller, setup_documents, setup_service):
    document_id = setup_service.get_documents(DocumentFilter())[0].id
    document = setup_controller.fetch_document_by_id(document_id)
    assert document is not None
    assert document.id == document_id

def teat_fetch_document_by_id_not_found(setup_controller):
    res = setup_controller.fetch_document_by_id("nonexistent-id")
    assert res.status_code == 404

def test_upload_document_success(setup_controller):
    new_document = {
        "file": UploadFile(filename="sample.txt", file=BytesIO(b"Sample content")),
        "type": "txt",
        "title": "New Document",
        "object_name": "new_doc.txt",
    }
    response = setup_controller.upload_document(**new_document)
    assert response["detail"] == "Document created successfully!"

def test_upload_document_invalid_type(setup_controller):
    invalid_document = {
        "file": UploadFile(filename="sample.txt", file=BytesIO(b"Sample content")),
        "type": "invalid_type",
        "title": "Invalid Document",
        "object_name": "invalid_doc.txt",
    }
    with pytest.raises(HTTPException) as exc:
        setup_controller.upload_document(**invalid_document)
    assert exc.value.status_code == 400
    assert exc.value.detail == "Document Type is not valid"

def test_upload_document_missing_title(setup_controller):
    document_missing_title = {
        "file": UploadFile(filename="sample.txt", file=BytesIO(b"Sample content")),
        "type": "txt",
        "title": "",  # Empty title should trigger DocumentTitleError
        "object_name": "new_doc_no_title.txt",
    }
    with pytest.raises(HTTPException) as exc:
        setup_controller.upload_document(**document_missing_title)
    assert exc.value.status_code == 400
    assert exc.value.detail == "Document title is required"

def test_upload_document_duplicate_name(setup_controller, setup_documents):
    duplicate_document = {
        "file": UploadFile(filename="sample.txt", file=BytesIO(b"Sample content")),
        "type": "txt",
        "title": "Duplicate Document",
        "object_name": "doc1.csv",  # Name that already exists in setup_documents
    }
    with pytest.raises(HTTPException) as exc:
        setup_controller.upload_document(**duplicate_document)
    assert exc.value.status_code == 400
    assert exc.value.detail == "Object name is required"
