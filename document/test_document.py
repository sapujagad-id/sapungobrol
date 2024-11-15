from pydantic import ValidationError
import pytest
from datetime import datetime
from uuid import uuid4
from document import Document, DocumentTitleError, DocumentType, DocumentTypeError, ObjectNameError

# Helper to create a valid document
def create_valid_document():
    return Document(
        id=uuid4(),
        type=DocumentType.CSV,
        title="Sample Document",
        object_name="sample.csv",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        access_level=0
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
                updated_at=None,
                access_level=None
            )
        assert len(excinfo.value.errors()) > 0  # Multiple validation errors raised