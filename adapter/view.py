from abc import ABC, abstractmethod

from fastapi import Request, HTTPException
from fastapi.templating import Jinja2Templates
from jinja2 import Environment
import jinja2

from starlette.status import HTTP_403_FORBIDDEN

from auth.controller import AuthController

from .slack_dto import SlackConfig

class SlackView(ABC):
    @abstractmethod
    def install(self, request: Request): # pragma: no cover
        pass

class SlackViewV1(SlackView):    
    def __init__(self, auth_controller: AuthController, slack_config:SlackConfig, admin_emails:list[str]) -> None:
        super().__init__()
        self.templates = Jinja2Templates(
            env=Environment(
                loader=jinja2.FileSystemLoader(["adapter/templates", "bot/templates"]),
                autoescape=True,
            )
        )
        self.auth_controller = auth_controller
        self.client_id = slack_config.slack_client_id
        self.admin_emails = admin_emails
        self.slack_scopes = slack_config.slack_scopes
    
    def install(self, request: Request):
        user_profile = self.auth_controller.user_profile_google(request)
        user_profile_data = user_profile.get("data")

        if user_profile_data.email not in self.admin_emails:
           raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Access denied")

        slack_scopes_string = ", ".join(self.slack_scopes)
        oauth_url = f"https://slack.com/oauth/v2/authorize?client_id={self.client_id}&scope={slack_scopes_string}&user_scope="
        return self.templates.TemplateResponse(
            request=request, 
            name="slack-install.html",
            context={
                "oauth_url": oauth_url,
                "admin_emails": self.admin_emails,
                "user_profile": user_profile.get("data")
            }
        )
