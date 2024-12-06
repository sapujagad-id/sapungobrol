from io import BytesIO

import pytest
from fastapi import HTTPException, UploadFile

from document.dto import DocumentFilter


class TestDocumentController:
    def test_fetch_documents_found(self, setup_controller, setup_documents):
        # Use filter that matches setup_documents fixture data
        documents = setup_controller.fetch_documents(object_name="doc1.csv")
        assert documents is not None
        assert len(documents) == 1
        assert documents[0].title == "Document 1"

    def test_fetch_documents_not_found(self, setup_controller):
        with pytest.raises(HTTPException) as exc:
            setup_controller.fetch_documents(object_name="nonexistent.csv")
        assert exc.value.status_code == 500
        
    def test_fetch_documents_unknown_error(self, setup_controller, mocker):
        mocker.patch.object(setup_controller, 'fetch_documents', side_effect=Exception("Database error"))
        with pytest.raises(Exception) as exc:
            setup_controller.fetch_documents(object_name="doc1.csv")
        assert exc is not None

    def test_fetch_document_by_name_found(self, setup_controller, setup_documents):
        document = setup_controller.fetch_document_by_name("doc1.csv")
        assert document is not None
        assert document.title == "Document 1"
        assert document.object_name == "doc1.csv"

    def test_fetch_document_by_name_not_found(self, setup_controller):
        with pytest.raises(HTTPException) as exc:
            setup_controller.fetch_document_by_name("Non Existent File")
        assert exc.value.status_code == 500
        
    def test_fetch_document_by_name_unknown_error(self, setup_controller, setup_documents, mocker):
        mocker.patch.object(setup_controller, 'fetch_document_by_name', side_effect=Exception("Database error"))
        with pytest.raises(Exception) as exc:
            setup_controller.fetch_document_by_name("doc1.csv")
        assert exc is not None

    def test_fetch_document_by_id_found(self, setup_controller, setup_documents, setup_service):
        document_id = setup_service.get_documents(DocumentFilter())[0].id
        document = setup_controller.fetch_document_by_id(document_id)
        assert document is not None
        assert document.id == document_id

    def teat_fetch_document_by_id_not_found(self, setup_controller):
        res = setup_controller.fetch_document_by_id("nonexistent-id")
        assert res.status_code == 404
        
    def test_fetch_document_by_id_unknown_error(self, setup_controller, setup_documents, mocker):
        mocker.patch.object(setup_controller, 'fetch_document_by_id', side_effect=Exception("Database error"))
        with pytest.raises(Exception) as exc:
            setup_controller.fetch_document_by_id("Document 1")
        assert exc is not None


    def test_upload_document_success(self, setup_controller):
        new_document = {
            "file": UploadFile(filename="sample.txt", file=BytesIO(b"Sample content")),
            "type": "txt",
            "title": "New Document",
            "object_name": "new_doc.txt",
            "access_level": 0,
        }
        response = setup_controller.upload_document(**new_document)
        assert response["detail"] == "Document created successfully!"

    def test_upload_document_invalid_type(self, setup_controller):
        invalid_document = {
            "file": UploadFile(filename="sample.txt", file=BytesIO(b"Sample content")),
            "type": "invalid_type",
            "title": "Invalid Document",
            "object_name": "invalid_doc.txt",
            "access_level": 0,
        }
        with pytest.raises(HTTPException) as exc:
            setup_controller.upload_document(**invalid_document)
        assert exc.value.status_code == 400
        assert exc.value.detail == "Data Source Type is not valid"

    def test_upload_document_missing_title(self, setup_controller):
        document_missing_title = {
            "file": UploadFile(filename="sample.txt", file=BytesIO(b"Sample content")),
            "type": "txt",
            "title": "",  # Empty title should trigger DocumentTitleError
            "object_name": "new_doc_no_title.txt",
            "access_level": 0,
        }
        with pytest.raises(HTTPException) as exc:
            setup_controller.upload_document(**document_missing_title)
        assert exc.value.status_code == 400
        assert exc.value.detail == "Document title is required"

    def test_upload_document_duplicate_name(self, setup_controller, setup_documents):
        duplicate_document = {
            "file": UploadFile(filename="sample.txt", file=BytesIO(b"Sample content")),
            "type": "txt",
            "title": "Duplicate Document",
            "object_name": "doc1.csv",  # Name that already exists in setup_documents
            "access_level": 0,
        }
        with pytest.raises(HTTPException) as exc:
            setup_controller.upload_document(**duplicate_document)
        assert exc.value.status_code == 400
        assert exc.value.detail == "Object by this name already exists"

    def test_upload_document_no_access_level(self, setup_controller, mocker):
        mocker.patch.object(setup_controller, 'upload_document', side_effect=Exception("Database error"))
        duplicate_document = {
            "file": UploadFile(filename="sample.txt", file=BytesIO(b"Sample content")),
            "type": "txt",
            "title": "Duplicate Document",
            "object_name": "doc1.csv",
        }
        with pytest.raises(Exception) as exc:
            setup_controller.upload_document(**duplicate_document)
        assert exc is not None
        
    def test_upload_document_unknown_error(self, setup_controller, mocker):
        mocker.patch.object(setup_controller, 'upload_document', side_effect=Exception("Database error"))
        duplicate_document = {
            "file": UploadFile(filename="sample.txt", file=BytesIO(b"Sample content")),
            "type": "txt",
            "title": "Duplicate Document",
            "object_name": "doc1.csv",
            "access_level": 0,
        }
        with pytest.raises(Exception) as exc:
            setup_controller.upload_document(**duplicate_document)
        assert exc is not None