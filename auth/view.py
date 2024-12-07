from abc import ABC, abstractmethod

import jinja2
from fastapi import Request
from fastapi.templating import Jinja2Templates
from jinja2 import Environment

from auth.controller import AuthController
from auth.service import AuthService


class UserView(ABC):
    @abstractmethod
    def view_users(self, request: Request):
        pass
      
class UserViewV1(UserView):    
    def __init__(self, controller: AuthController, service: AuthService) -> None:
        super().__init__()
        self.templates = Jinja2Templates(
            env=Environment(
                loader=jinja2.FileSystemLoader(['auth/templates', "components/templates"]),
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
                    "user_profile": user_profile.get("data")
            },
        )
        
    def view_invalid_login_email(self, request:Request):
        return self.templates.TemplateResponse(
            request=request,
            name="invalid-email.html",
        )
    