from abc import ABC, abstractmethod
from fastapi import Request
from fastapi.templating import Jinja2Templates
from jinja2 import Environment
import jinja2

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
                loader=jinja2.FileSystemLoader(['data_source/templates', 'bot/templates']),
                autoescape=True,
            )
        )
        self.auth_controller = auth_controller

    @login_required()
    def show_list_data_sources(self, request: Request):
        pass
