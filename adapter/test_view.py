import pytest
from unittest.mock import Mock
from fastapi import Request, HTTPException
from jose import jwt
from datetime import datetime, timedelta, timezone

from .view import SlackViewV1
from .slack_dto import SlackConfig
from auth.controller import AuthControllerV1
from auth.repository import PostgresAuthRepository
from auth.service import AuthServiceV1


@pytest.fixture()
def setup_service():
    """Set up a mocked service."""
    service = Mock(spec=AuthServiceV1)
    service.repository = Mock(spec=PostgresAuthRepository)
    
    return service

@pytest.fixture
def setup_controller(setup_service):
    """Set up a mocked AuthController."""
    controller = AuthControllerV1(setup_service)
    return controller

@pytest.fixture
def setup_jwt_secret():
    """Provide a JWT secret for encoding tokens."""
    return "some_secret_string"

class MockUserProfile:
    def __init__(self, email):
        self.email = email


class TestSlackViewV1:

    @pytest.mark.asyncio
    async def test_install_authorized(self, setup_controller, setup_jwt_secret):
        slack_config = SlackConfig(
            slack_bot_token="",
            slack_signing_secret="",
            slack_client_id="test_client_id",
            slack_client_secret="",
            slack_scopes=["channels:history", "chat:write"],
        )
        slack_view = SlackViewV1(
            auth_controller=setup_controller,
            slack_config=slack_config,
            admin_emails=["admin@broom.id"]
        )

        request = Mock(spec=Request)

        token = jwt.encode({
            "email": "admin@broom.id",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }, setup_jwt_secret, algorithm="HS256")

        request.cookies = {"token": token}

        setup_controller.user_profile_google = Mock(return_value={"data": MockUserProfile("admin@broom.id")})

        response = await slack_view.install(request, testing=True)

        assert response.template.name == "slack-install.html"
        assert "oauth_url" in response.context
        assert "user_profile" in response.context

    @pytest.mark.asyncio
    async def test_install_unauthorized(self, setup_controller, setup_jwt_secret):
        slack_config = SlackConfig(
            slack_bot_token="",
            slack_signing_secret="",
            slack_client_id="test_client_id",
            slack_client_secret="",
            slack_scopes=["channels:history", "chat:write"],
        )

        slack_view = SlackViewV1(
            auth_controller=setup_controller,
            slack_config=slack_config,
            admin_emails=["admin@broom.id"]
        )

        request = Mock(spec=Request)

        token = jwt.encode({
            "email": "user@broom.id",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1)
        }, setup_jwt_secret, algorithm="HS256")

        request.cookies = {"token": token}

        setup_controller.user_profile_google = Mock(return_value={"data": MockUserProfile("user@broom.id")})

        with pytest.raises(HTTPException) as exc_info:
            await slack_view.install(request, testing=True)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Access denied"
