from abc import ABC, abstractmethod

import jinja2
from fastapi import Request
from fastapi.templating import Jinja2Templates
from jinja2 import Environment

from auth.controller import AuthController
from auth.middleware import login_required


class DataSourceView(ABC):
    @abstractmethod
    def show_list_data_sources(self, request: Request):
        pass

class DataSourceViewV1(DataSourceView):
    def __init__(self, auth_controller: AuthController) -> None:
        super().__init__()
        self.templates = Jinja2Templates(
            env=Environment(
                loader=jinja2.FileSystemLoader(['data_source/templates', 'components/templates']),
                autoescape=True,
            )
        )
        self.auth_controller = auth_controller

    @login_required()
    def show_list_data_sources(self, request: Request):
        data_sources = [
            {"id": "1", "name": "Source One", "type": "API", "last_updated": "2024-10-01", "description": "Primary data source"},
            {"id": "2", "name": "Source Two", "type": "Database", "last_updated": "2024-09-15", "description": "User data and metrics"},
            {"id": "3", "name": "Source Three", "type": "CSV", "last_updated": "2024-08-20", "description": "Archived records"},
        ]
        user_profile = self.auth_controller.user_profile_google(request)
        return self.templates.TemplateResponse(
            request=request, 
            name="data-source-list.html", 
            context={
                "data_sources": data_sources,
                "user_profile": user_profile.get("data")
            }
        )
