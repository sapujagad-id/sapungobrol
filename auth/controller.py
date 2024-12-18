from abc import ABC, abstractmethod

from fastapi import HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from jose import ExpiredSignatureError, JWTError
from loguru import logger

from auth.dto import ProfileResponse, EditUserAccess
from auth.exceptions import (
    NoTokenSupplied,
    UserNotFound,
    UserUnauthorized,
    InvalidAccessLevel,
)
from auth.service import AuthService


class AuthController(ABC):
    @abstractmethod
    async def logout(self):
        pass

    @abstractmethod
    async def login_redirect_google(self) -> RedirectResponse:
        pass

    @abstractmethod
    async def authorize_google(self, request: Request, code: str) -> Response:
        pass

    @abstractmethod
    def get_all_users_basic_info(self, request: Request):
        pass

    @abstractmethod
    def edit_user_access(self, user_id: str, body: EditUserAccess) -> dict[str, str]:
        pass

    @abstractmethod
    async def user_profile_google(self, request: Request) -> ProfileResponse:
        pass


class AuthControllerV1(AuthController):
    def __init__(self, service: AuthService) -> None:
        super().__init__()
        self.service = service
        self.logger = logger.bind(service="AuthController")

    def logout(self) -> Response:
        response = RedirectResponse("/")
        try:
            response.delete_cookie("token")
            response.delete_cookie("is_admin")
        except:
            pass
        return response

    def login_redirect_google(self) -> Response:
        response = self.service.login_redirect_google()
        return response

    def authorize_google(self, request: Request, code: str) -> Response:
        response = self.service.authorize_google(request, code)

        return response

    def get_all_users_basic_info(self, request: Request):
        token = request.cookies.get("token")
        try:
            all_user = self.service.get_all_users_basic_info(token)
            return all_user
        except (NoTokenSupplied, UserUnauthorized):
            raise HTTPException(status_code=401, detail="You are not authenticated")
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=400, detail="Your token has expired, please login again"
            )
        except JWTError:
            raise HTTPException(status_code=400, detail="Invalid token signature")
        except UserNotFound:
            raise HTTPException(status_code=404, detail="User not found")

    # This will be tested later
    def edit_user_access(
        self, user_id: str, body: EditUserAccess
    ) -> dict[str, str]:  # pragma: no cover
        try:
            self.service.edit_user_access(user_id, body)
            return {"message": "Access level updated successfully"}
        except InvalidAccessLevel:
            raise HTTPException(
                status_code=400, detail=InvalidAccessLevel.default_message
            )

    def user_profile_google(self, request: Request) -> ProfileResponse:
        token = request.cookies.get("token")
        try:
            user = self.service.get_user_profile(token)
            return ProfileResponse(
                data=user,
            )
        except NoTokenSupplied:
            raise HTTPException(status_code=401, detail="You are not authenticated")
        except ExpiredSignatureError:
            raise HTTPException(
                status_code=400, detail="Your token has expired, please login again"
            )
        except JWTError:
            raise HTTPException(status_code=400, detail="Invalid token signature")
        except UserNotFound:
            raise HTTPException(status_code=404, detail="User not found")
