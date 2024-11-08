from abc import ABC, abstractmethod
from fastapi import Request
from fastapi.templating import Jinja2Templates
from jinja2 import Environment
import jinja2

from auth.controller import AuthController
from auth.middleware import login_required
from document.dto import DocumentFilter
from document.service import DocumentService

class DocumentView(ABC):
    @abstractmethod
    def show_list_documents(self, request: Request):
        pass

class DocumentViewV1(DocumentView):
    def __init__(self, document_service: DocumentService, auth_controller: AuthController) -> None:
        super().__init__()
        self.templates = Jinja2Templates(
            env=Environment(
                loader=jinja2.FileSystemLoader(['document/templates', 'bot/templates']),
                autoescape=True,
            )
        )
        self.auth_controller = auth_controller
        self.service = document_service

    @login_required()
    def show_list_documents(self, request: Request):
        documents = self.service.get_documents(DocumentFilter())
        user_profile = self.auth_controller.user_profile_google(request)
        return self.templates.TemplateResponse(
            request=request, 
            name="document-list.html", 
            context={
                "documents": documents,
                "user_profile": user_profile.get("data")
            }
        )
