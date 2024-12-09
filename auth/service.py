import base64
from abc import ABC, abstractmethod
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import requests
from fastapi import HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from jose import jwt
from loguru import logger
from uuid import UUID

from auth.dto import GoogleCredentials, EditUserAccess
from auth.repository import AuthRepository
from auth.user import GoogleUserInfo, User

from .exceptions import (
    NoTokenSupplied,
    UserNotFound,
    UserUnauthorized,
    InvalidAccessLevel,
)


class AuthService(ABC):
    @abstractmethod
    def authorize_google(
        self, request: Request, user_info_json: GoogleUserInfo
    ) -> Response:
        pass

    @abstractmethod
    def login_redirect_google(self) -> Response:
        pass

    @abstractmethod
    def get_user_profile(self, token: str) -> User:
        pass

    @abstractmethod
    def get_all_users_basic_info(self, token: str) -> User:
        pass

    @abstractmethod
    def edit_user_access(self, user_id: str, body: EditUserAccess):
        pass


class AuthServiceV1(AuthService):
    def __init__(
        self,
        repository: AuthRepository,
        google_credentials: GoogleCredentials,
        base_url: str,
        jwt_secret: str,
        admin_emails: list[str],
        total_access_levels: int,
    ) -> None:
        super().__init__()
        self.repository = repository
        self.google_credentials = google_credentials
        self.base_url = base_url
        self.logger = logger.bind(service="AuthService")
        self.jwt_secret = jwt_secret
        self.admin_emails = admin_emails
        self.total_access_levels = total_access_levels

    def login_redirect_google(self) -> Response:
        query_params = urlencode(
            {
                "response_type": "code",
                "client_id": self.google_credentials.client_id,
                "redirect_uri": self.google_credentials.redirect_uri,
                "scope": "openid profile email",
                "access_type": "offline",
                "prompt": "select_account",
            }
        )
        return RedirectResponse(
            f"https://accounts.google.com/o/oauth2/auth?{query_params}"
        )

    def authorize_google(self, request: Request, code: str) -> Response:
        JWT_EXPIRY_IN_HOURS = 24

        data = {
            "code": code,
            "client_id": self.google_credentials.client_id,
            "client_secret": self.google_credentials.client_secret,
            "redirect_uri": self.google_credentials.redirect_uri,
            "grant_type": "authorization_code",
        }

        # get oauth token from google
        response = requests.post(
            url="https://accounts.google.com/o/oauth2/token", data=data
        )
        response.raise_for_status()
        access_token = response.json().get("access_token")

        # get user info using token
        user_info = requests.get(
            url="https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        self.logger.debug("user_info with token", user_info)
        user_info.raise_for_status()
        user_info_json: GoogleUserInfo = user_info.json()

        # check if the email is a valid broom email
        if not user_info_json["email"].endswith("@broom.id"):
            return RedirectResponse("/invalid-email")

        # store user in DB
        self.logger.debug("user_info_json with user data", user_info_json)
        user = self.repository.find_user_by_sub(user_info_json["sub"])
        if not user:
            self.repository.add_google_user(user_info_json)

        # generate our own access token
        jwt_token = jwt.encode(
            {
                "sub": user_info_json["sub"],
                "email": user_info_json["email"],
                "exp": datetime.now(UTC) + timedelta(hours=JWT_EXPIRY_IN_HOURS),
            },
            self.jwt_secret,
        )
        # redirect to page based on state
        target_path = "/"

        state = request.cookies.get("oauth_state")
        if state is not None:
            cleaned_state = state.removeprefix("b'").removesuffix("'")
            target_path = base64.urlsafe_b64decode(cleaned_state).decode("utf-8")

        target_url = self.base_url + target_path
        response = RedirectResponse(url=target_url)
        response.set_cookie(
            key="token",
            value=jwt_token,
            httponly=True,
            secure=True,
        )
        response.set_cookie(
            key="is_admin",
            value=user_info_json["email"] in self.admin_emails,
            httponly=True,
            secure=True,
        )

        return response

    def get_user_profile(self, token: str) -> User:
        self.logger.debug("jwt token", token)
        if token == "" or token == None:
            raise NoTokenSupplied

        decoded = jwt.decode(
            token=token,
            key=self.jwt_secret,
            algorithms=["HS256"],
        )
        self.logger.debug("decoded jwt", decoded.items())

        user = self.repository.find_user_by_email(decoded["email"])
        if not user:
            raise UserNotFound
        return user

    def get_all_users_basic_info(self, token: str) -> User:
        self.logger.debug("jwt token", token)
        if token == "" or token == None:
            raise NoTokenSupplied

        decoded = jwt.decode(
            token=token,
            key=self.jwt_secret,
            algorithms=["HS256"],
        )
        self.logger.debug("decoded jwt", decoded.items())

        if decoded["email"] not in self.admin_emails:
            raise UserUnauthorized

        users = self.repository.get_all_users_basic_info()
        return users

    # This will be tested later
    def edit_user_access(self, user_id: str, body: EditUserAccess):  # pragma: no cover
        if body.access_level < 1 or body.access_level > self.total_access_levels:
            raise InvalidAccessLevel

        try:
            user_id_uuid = UUID(user_id, version=4)

            self.repository.update_user_access(
                user_id=user_id_uuid, access_level=body.access_level
            )
        except ValueError:
            raise UserNotFound
