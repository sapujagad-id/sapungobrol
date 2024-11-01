import pytest
from unittest.mock import Mock
from fastapi import Request
from datetime import datetime, timedelta
from jose import jwt
from uuid import uuid4

from .view import DataSourceViewV1  # Update with the correct import for your view class

@pytest.mark.asyncio
class TestDataSourceView:
    @pytest.mark.asyncio
    async def test_show_list_data_sources(self, setup_view, setup_jwt_secret, dummy_user_profile):
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

        # Mock the user_profile_google method
        view.auth_controller.user_profile_google = Mock(return_value=dummy_user_profile)

        # Call the view method
        response = await view.show_list_data_sources(request=request)

        # Check that the correct template is used and context is passed
        assert response.template.name == "data-source-list.html"
        assert "data_sources" in response.context
        assert len(response.context["data_sources"]) == 3
        assert "user_profile" in response.context
        assert response.context["user_profile"].get('email') == dummy_user_profile.get("data")["email"]

        # Validate if data source names are present in the rendered template
        rendered = response.body.decode()  # Decode response body for assertion
        assert 'List of Data Sources' in rendered
        assert 'Source One' in rendered
        assert 'Source Two' in rendered
        assert 'API' in rendered
        assert 'Database' in rendered
        assert 'Primary data source' in rendered
        assert 'User data and metrics' in rendered
