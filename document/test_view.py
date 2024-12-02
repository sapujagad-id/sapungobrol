import pytest
from unittest.mock import Mock
from fastapi import Request
from datetime import datetime, timedelta
from jose import jwt
from uuid import uuid4

from auth.dto import ProfileResponse
from auth.user import User
from document.document import DocumentType

from .view import DocumentViewV1  # Update with the correct import for your view class

class TestDocumentView:
    def test_show_list_document(self, setup_view, setup_jwt_secret, dummy_user_profile):
        view = setup_view

        # Create a mock request
        request = Mock(spec=Request)

        # Encode a token using the provided JWT secret from the fixture
        token = jwt.encode({
            "sub": "test_sub",
            "email": "test@broom.id",
            "exp": datetime.now() + timedelta(hours=3)
        }, setup_jwt_secret)

        # Set the cookies on the request mock
        request.cookies = {'token': token}

        mock_documents = [
            {"title": "Document 1", "type": "pdf", "object_name": "doc1.pdf", "created_at": datetime(2023, 10, 1), "updated_at": datetime(2024, 10, 1)},
            {"title": "Document 2", "type": "text", "object_name": "doc2.txt", "created_at": datetime(2023, 10, 1), "updated_at": datetime(2024, 10, 1)},
            {"title": "Document 3", "type": "csv", "object_name": "doc3.csv", "created_at": datetime(2023, 10, 1), "updated_at": datetime(2024, 10, 1)},
        ]
        view.service.get_documents = Mock(return_value=mock_documents)
        view.auth_controller.user_profile_google = Mock(return_value=dummy_user_profile)

        # Call the view method
        response = view.show_list_documents(request=request)

        # Check that the correct template is used and context is passed
        assert response.template.name == "document-list.html"
        assert "documents" in response.context
        assert len(response.context["documents"]) == 3
        assert "user_profile" in response.context
        assert response.context["user_profile"].get('email') == dummy_user_profile.get("data")["email"]

        # Validate if data source names are present in the rendered template
        rendered = response.body.decode()  # Decode response body for assertion
        assert 'List of Documents' in rendered
        assert 'Document 3' in rendered
        assert 'pdf' in rendered
        assert 'doc2.txt' in rendered
        
    def test_show_create_document_form(self, setup_view, setup_jwt_secret, dummy_user_profile):
        view = setup_view

        # Create a mock request
        request = Mock(spec=Request)

        # Encode a token using the provided JWT secret from the fixture
        token = jwt.encode({
            "sub": "test_sub",
            "email": "test@broom.id",
            "exp": datetime.now() + timedelta(hours=3)
        }, setup_jwt_secret)

        # Set the cookies on the request mock
        request.cookies = {'token': token}
        view.auth_controller.user_profile_google = Mock(return_value=ProfileResponse(data=User(
            id=uuid4(),
            sub="asdasdadsad",
            name="asd",
            email="test@broom.id",
            email_verified=True,
            created_at="2024-10-24T00:00:00Z",
            picture="https://image.com",
            access_level=7,
            login_method="Google",
        )))

        # Call the view method
        response = view.new_document_view(request=request)

        # Check that the correct template is used and context is passed
        assert response.template.name == "new-document.html"
        assert "document_types" in response.context
        assert response.context["document_types"] == [x.lower() for x in DocumentType._member_names_]
        assert "access_levels" in response.context
        assert 0 in response.context["access_levels"]
        assert len(response.context["access_levels"]) > 0