from abc import ABC, abstractmethod

from fastapi import Request
from fastapi.templating import Jinja2Templates
from jinja2 import Environment
import jinja2

from auth.controller import AuthController
from auth.service import AuthService


class UserView(ABC):
    @abstractmethod
    def view_users(self, request: Request):
        pass
      
class UserViewV1(UserView):    
    def __init__(self, controller: AuthController, service: AuthService, admin_emails:list[str]) -> None:
        super().__init__()
        self.templates = Jinja2Templates(
            env=Environment(
                loader=jinja2.FileSystemLoader(['auth/templates', "bot/templates"]),
                autoescape=True,
            )
        )
        self.controller = controller
        self.service = service 
        self.admin_emails = admin_emails

       
    def view_users(self, request: Request):
        users = self.controller.get_all_users_basic_info(request)
        user_profile = self.controller.user_profile_google(request)

        return self.templates.TemplateResponse(
                request=request, 
                name="view-users.html",
                context={
                    "users": users,
                    "admin_emails": self.admin_emails,
                    "user_profile": user_profile.get("data")
            },
        )
    
    