from unittest.mock import Mock

import pytest
from fastapi import HTTPException, Response
from fastapi.responses import RedirectResponse
from jose import ExpiredSignatureError, JWTError

from auth.exceptions import NoTokenSupplied, UserNotFound, UserUnauthorized
from auth.repository import UserModel


class TestAuthController:
    def test_logout(self, setup_controller):
        response = setup_controller.logout()
        assert isinstance(response, Response)
        assert response.headers["location"] == "/"
        assert response.status_code == 307

    def test_login_redirect_google(self, setup_controller, setup_service):
        setup_service.login_redirect_google.return_value = RedirectResponse(url="/redirect-url")
        response = setup_controller.login_redirect_google()
        assert isinstance(response, RedirectResponse)
        assert response.status_code == 307
        setup_service.login_redirect_google.assert_called_once()

    def test_authorize_google(self, setup_controller, setup_service):
        request = Mock()
        setup_service.authorize_google.return_value = RedirectResponse(url="/")
        response = setup_controller.authorize_google(request, "auth_code")
        assert isinstance(response, RedirectResponse)
        assert response.headers["location"] == "/"
        setup_service.authorize_google.assert_called_once_with(request, "auth_code")

    def test_user_profile_google_success(self, setup_controller, setup_service):
        request = Mock()
        request.cookies.get.return_value = "valid_token"
        setup_service.get_user_profile.return_value = UserModel()

        response = setup_controller.user_profile_google(request)
        assert isinstance(response["data"], UserModel)
        setup_service.get_user_profile.assert_called_once_with("valid_token")

    def test_user_profile_google_no_token(self, setup_controller, setup_service):
        request = Mock()
        request.cookies.get.return_value = None
        setup_service.get_user_profile.side_effect = NoTokenSupplied

        with pytest.raises(HTTPException) as excinfo:
            setup_controller.user_profile_google(request)
        assert excinfo.value.status_code == 401
        assert excinfo.value.detail == "You are not authenticated"

    def test_user_profile_google_invalid_token(self, setup_controller, setup_service):
        request = Mock()
        request.cookies.get.return_value = "invalid_token"
        setup_service.get_user_profile.side_effect = JWTError

        with pytest.raises(HTTPException) as excinfo:
            setup_controller.user_profile_google(request)
        assert excinfo.value.status_code == 400
        assert excinfo.value.detail == "Invalid token signature"

    def test_user_profile_google_token_expired(self, setup_controller, setup_service):
        request = Mock()
        request.cookies.get.return_value = "expired_token"
        setup_service.get_user_profile.side_effect = ExpiredSignatureError

        with pytest.raises(HTTPException) as excinfo:
            setup_controller.user_profile_google(request)
        assert excinfo.value.status_code == 400
        assert excinfo.value.detail == "Your token has expired, please login again"

    def test_user_profile_google_user_not_found(self, setup_controller, setup_service):
        request = Mock()
        request.cookies.get.return_value = "valid_token"
        setup_service.get_user_profile.side_effect = UserNotFound

        with pytest.raises(HTTPException) as excinfo:
            setup_controller.user_profile_google(request)
        assert excinfo.value.status_code == 404
        assert excinfo.value.detail == "User not found"

    def test_get_all_users_basic_info_success(self, setup_controller, setup_service):
        request = Mock()
        request.cookies.get.return_value = "valid_token"
        setup_service.get_all_users_basic_info.return_value = [{"name": "John Doe", "email": "johndoe@example.com"}]

        response = setup_controller.get_all_users_basic_info(request)

        assert response == [{"name": "John Doe", "email": "johndoe@example.com"}]
        setup_service.get_all_users_basic_info.assert_called_once_with("valid_token")

    def test_get_all_users_basic_info_no_token(self, setup_controller, setup_service):
        request = Mock()
        request.cookies.get.return_value = None
        setup_service.get_all_users_basic_info.side_effect = NoTokenSupplied

        with pytest.raises(HTTPException) as excinfo:
            setup_controller.get_all_users_basic_info(request)

        assert excinfo.value.status_code == 401
        assert excinfo.value.detail == "You are not authenticated"

    def test_get_all_users_basic_info_user_unauthorized(self, setup_controller, setup_service):
        request = Mock()
        request.cookies.get.return_value = "unauthorized_token"
        setup_service.get_all_users_basic_info.side_effect = UserUnauthorized

        with pytest.raises(HTTPException) as excinfo:
            setup_controller.get_all_users_basic_info(request)

        assert excinfo.value.status_code == 401
        assert excinfo.value.detail == "You are not authenticated"

    def test_get_all_users_basic_info_token_expired(self, setup_controller, setup_service):
        request = Mock()
        request.cookies.get.return_value = "expired_token"
        setup_service.get_all_users_basic_info.side_effect = ExpiredSignatureError

        with pytest.raises(HTTPException) as excinfo:
            setup_controller.get_all_users_basic_info(request)

        assert excinfo.value.status_code == 400
        assert excinfo.value.detail == "Your token has expired, please login again"

    def test_get_all_users_basic_info_invalid_token(self, setup_controller, setup_service):
        request = Mock()
        request.cookies.get.return_value = "invalid_token"
        setup_service.get_all_users_basic_info.side_effect = JWTError

        with pytest.raises(HTTPException) as excinfo:
            setup_controller.get_all_users_basic_info(request)

        assert excinfo.value.status_code == 400
        assert excinfo.value.detail == "Invalid token signature"

    def test_get_all_users_basic_info_user_not_found(self, setup_controller, setup_service):
        request = Mock()
        request.cookies.get.return_value = "valid_token"
        setup_service.get_all_users_basic_info.side_effect = UserNotFound

        with pytest.raises(HTTPException) as excinfo:
            setup_controller.get_all_users_basic_info(request)

        assert excinfo.value.status_code == 404
        assert excinfo.value.detail == "User not found"