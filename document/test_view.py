import pytest
from unittest.mock import Mock
from fastapi import Request
from datetime import datetime, timedelta
from jose import jwt
from uuid import uuid4

from .view import DocumentViewV1  # Update with the correct import for your view class

@pytest.mark.asyncio
class TestDocumentView:
    @pytest.mark.asyncio
    async def test_show_list_document(self, setup_view, setup_jwt_secret, dummy_user_profile):
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
        response = await view.show_list_documents(request=request)

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