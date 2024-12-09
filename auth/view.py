from abc import ABC, abstractmethod

import jinja2
from fastapi import Request, HTTPException
from fastapi.templating import Jinja2Templates
from jinja2 import Environment

from auth.controller import AuthController
from auth.service import AuthService
from auth.exceptions import UserNotFound


class UserView(ABC):
    @abstractmethod
    def view_users(self, request: Request):
        pass

    @abstractmethod
    def edit_user_access_page(self, user_id: str, request: Request):
        pass


class UserViewV1(UserView):
    def __init__(self, controller: AuthController, service: AuthService) -> None:
        super().__init__()
        self.templates = Jinja2Templates(
            env=Environment(
                loader=jinja2.FileSystemLoader(
                    ["auth/templates", "components/templates"]
                ),
                autoescape=True,
            )
        )
        self.controller = controller
        self.service = service

    def view_users(self, request: Request):
        users = self.controller.get_all_users_basic_info(request)
        user_profile = self.controller.user_profile_google(request)

        return self.templates.TemplateResponse(
            request=request,
            name="view-users.html",
            context={
                "users": users,
                "is_admin": request.cookies.get("is_admin"),
                "user_profile": user_profile.get("data"),
            },
        )

    def view_invalid_login_email(self, request: Request):
        return self.templates.TemplateResponse(
            request=request,
            name="invalid-email.html",
        )

    # Will test later
    def edit_user_access_page(self, user_id: str, request: Request):  # pragma: no cover
        try:
            user = self.service.get_user_by_id(user_id)
            user_profile = self.controller.user_profile_google(request)
            total_access_levels = self.service.get_total_access_levels()
            return self.templates.TemplateResponse(
                request=request,
                name="edit-access-level.html",
                context={
                    "user_id": user_id,
                    "access_level": user.access_level,
                    "total_access_levels": total_access_levels,
                    "user_profile": user_profile.get("data"),
                    "is_admin": request.cookies.get("is_admin"),
                },
            )

        except UserNotFound:
            raise HTTPException(status_code=404, detail="User not found")
