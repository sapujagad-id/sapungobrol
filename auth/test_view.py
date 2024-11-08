import pytest
from unittest.mock import Mock
from fastapi import Request
from jose import jwt
from datetime import datetime, timedelta

from auth.view import UserViewV1

class TestUserView:

    @pytest.mark.asyncio
    async def test_view_users_success(self, setup_controller, setup_service, setup_jwt_secret):
        user_view = UserViewV1(controller=setup_controller, service=setup_service, admin_emails=["admin@broom.id", ])

        request = Mock(spec=Request)

        token = jwt.encode({
            "email": "admin@broom.id",
            "exp": datetime() + timedelta(hours=1)
        }, setup_jwt_secret, algorithm="HS256")

        request.cookies = {'token': token}

        setup_controller.get_all_users_basic_info = Mock(return_value=[
            {"name": "User1", "email": "user1@broom.id"},
            {"name": "User2", "email": "user2@broom.id"},
        ])
        setup_controller.user_profile_google = Mock(return_value={"data": {"email": "admin@broom.id"}})

        response = await user_view.view_users(request, testing=True)

        assert response.template.name == "view-users.html"
        assert "users" in response.context
        assert "user_profile" in response.context

        assert response.context["users"] == [
            {"name": "User1", "email": "user1@broom.id"},
            {"name": "User2", "email": "user2@broom.id"}
        ]
        assert response.context["user_profile"]["email"] == "admin@broom.id"

        rendered = response.body.decode()
        assert 'User1' in rendered
        assert 'User2' in rendered