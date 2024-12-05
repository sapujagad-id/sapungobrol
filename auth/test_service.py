from unittest.mock import patch, MagicMock
from fastapi.responses import RedirectResponse
import pytest
from fastapi import HTTPException
from auth.exceptions import NoTokenSupplied, UserNotFound, UserUnauthorized
from auth.service import AuthServiceV1
from jose import jwt
from datetime import UTC, datetime, timedelta

from auth.user import GoogleUserInfo

class MockRequest:
    def __init__(self, cookies):
        self.cookies = cookies
        
class TestAuthService:  

    def test_login_redirect_google_success(self, setup_real_service: AuthServiceV1):
        response = setup_real_service.login_redirect_google()
        assert response.status_code == 307
        assert "https://accounts.google.com/o/oauth2/auth?" in response.headers["location"]

    
    @patch('requests.post')
    @patch('requests.get')
    def test_authorize_google_success(self, mock_get, mock_post, setup_real_service: AuthServiceV1):
        mock_post.return_value.json.return_value = {"access_token": "fake_access_token"}
        mock_post.return_value.raise_for_status.return_value = None

        mock_get.return_value.json.return_value = {
            "sub": "12345",
            "email": "test@broom.id",
            "email_verified": True,
            "name": "Test User",
            "given_name": "Test User",
            "picture": "https://newuser.com/icon.png",
        }
        mock_get.return_value.raise_for_status.return_value = None
        mock_request = MockRequest(cookies={})
        response = setup_real_service.authorize_google(mock_request, "fake_code")

        assert isinstance(response, RedirectResponse)
        assert response.status_code == 302 or 307
        assert "token" in response.headers['set-cookie']

        # Verify JWT token
        token = response.headers['set-cookie'].split(';')[0].split('=')[1]
        decoded = jwt.decode(token, setup_real_service.jwt_secret, algorithms=["HS256"])
        assert decoded['sub'] == "12345"
        assert decoded['email'] == "test@broom.id"
        
    @patch('requests.post')
    @patch('requests.get')
    def test_authorize_google_not_broom(self, mock_get, mock_post, setup_real_service: AuthServiceV1):
        mock_post.return_value.json.return_value = {"access_token": "fake_access_token"}
        mock_post.return_value.raise_for_status.return_value = None

        mock_get.return_value.json.return_value = {
            "sub": "12345",
            "email": "notbroom@gmail.com",
            "email_verified": True,
            "name": "Test User",
            "given_name": "Test User",
            "picture": "https://newuser.com/icon.png",
        }
        mock_get.return_value.raise_for_status.return_value = None
        mock_request = MockRequest(cookies={})
        
        with pytest.raises(HTTPException):
            setup_real_service.authorize_google(mock_request, "fake_code")

    @patch('requests.post')
    def test_authorize_google_invalid_token(self, mock_post, setup_real_service):
        mock_post.return_value.raise_for_status.side_effect = HTTPException(status_code=400)

        mock_request = MockRequest(cookies={})

        with pytest.raises(HTTPException):
            setup_real_service.authorize_google(mock_request, "invalid_code")

    @patch('requests.post')
    @patch('requests.get')
    def test_authorize_google_existing_user(self, mock_get, mock_post, setup_real_service):
        mock_post.return_value.json.return_value = {"access_token": "fake_access_token"}
        mock_post.return_value.raise_for_status.return_value = None
        mock_get.return_value.json.return_value = {
            "sub": "12345",
            "email": "existing@broom.id",
            "name": "Existing User"
        }
        mock_get.return_value.raise_for_status.return_value = None

        # Set up an existing user
        setup_real_service.repository.add_google_user({
            "sub": "12345",
            "email": "existing@broom.id",
            "email_verified": True,
            "name": "Existing User",
            "given_name": "Existing User",
            "picture": "https://example.com/image.png",
        })

        mock_request = MockRequest(cookies={})

        response = setup_real_service.authorize_google(mock_request, "fake_code")

        assert isinstance(response, RedirectResponse)
        assert response.status_code == 302 or 307
        assert "token" in response.headers['set-cookie']
        
    def test_get_user_profile_success(self, setup_real_service: AuthServiceV1, setup_jwt_secret: str):
        token = jwt.encode({
            "sub": "test_sub", 
            "email": "test@broom.id", 
            "exp": datetime.now(UTC) + timedelta(hours=3)},
            setup_jwt_secret
        )
        user_info = GoogleUserInfo(
            sub="test_sub",
            name="New User",
            given_name="anewuser",
            picture="https://newuser.com/pic.png",
            email="test@broom.id",
            email_verified=True,
        )
        
        setup_real_service.repository.add_google_user(user_info)
        profile = setup_real_service.get_user_profile(token)
        assert profile is not None
        assert profile.email == "test@broom.id"

    def test_get_user_profile_no_token_supplied(self, setup_real_service: AuthServiceV1):
        with pytest.raises(NoTokenSupplied):
            setup_real_service.get_user_profile("")

    def test_get_user_profile_user_not_found(self, setup_real_service: AuthServiceV1):
        token = jwt.encode({
            "sub": "non_existent_sub", 
            "email": "nonexistent@broom.id",
            "exp": datetime.now(UTC) + timedelta(hours=3)},
            setup_real_service.jwt_secret,
        )
        with pytest.raises(UserNotFound):
            setup_real_service.get_user_profile(token)

    def test_get_all_users_basic_info_success(self, setup_real_service: AuthServiceV1):

        setup_real_service.admin_emails = ["admin@broom.id"]
        setup_real_service.jwt_secret = "testsecret"

        token = jwt.encode({"email": "admin@broom.id"}, setup_real_service.jwt_secret, algorithm="HS256")

        setup_real_service.repository.get_all_users_basic_info = MagicMock(return_value=[{"name": "User1", "email": "user1@broom.id"}])

        users = setup_real_service.get_all_users_basic_info(token)
        assert isinstance(users, list)
        assert users == [{"name": "User1", "email": "user1@broom.id"}]
        setup_real_service.repository.get_all_users_basic_info.assert_called_once()

    def test_get_all_users_basic_info_no_token(self, setup_real_service: AuthServiceV1):

        with pytest.raises(NoTokenSupplied):
            setup_real_service.get_all_users_basic_info("")

    def test_get_all_users_basic_info_unauthorized_user(self, setup_real_service: AuthServiceV1):

        setup_real_service.admin_emails = ["admin@broom.id"]
        setup_real_service.jwt_secret = "testsecret"

        token = jwt.encode({"email": "unauthorized@broom.id"}, setup_real_service.jwt_secret, algorithm="HS256")

        with pytest.raises(UserUnauthorized):
            setup_real_service.get_all_users_basic_info(token)