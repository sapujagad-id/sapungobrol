from abc import ABC, abstractmethod
from fastapi import Request
from fastapi.templating import Jinja2Templates
from jinja2 import Environment
import jinja2
from loguru import logger

from auth.controller import AuthController
from document.document import DocumentType
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
                loader=jinja2.FileSystemLoader(['document/templates', 'components/templates']),
                autoescape=True,
            )
        )
        self.auth_controller = auth_controller
        self.service = document_service
        self.logger = logger.bind(service="DocumentView")

    def show_list_documents(self, request: Request):
        documents = self.service.get_documents(DocumentFilter())
        user_profile = self.auth_controller.user_profile_google(request)
        return self.templates.TemplateResponse(
            request=request, 
            name="document-list.html", 
            context={
                "documents": documents,
                "user_profile": user_profile.get("data"),
                "is_admin": request.cookies.get("is_admin"),
            }
        )
        
    def new_document_view(self, request: Request):
        user_profile = self.auth_controller.user_profile_google(request)
        max_level = user_profile.get('data').access_level
        self.logger.info(f"user has access level {max_level}")
        return self.templates.TemplateResponse(
            request=request, 
            name="new-document.html", 
            context={
                "document_types": [x.lower() for x in DocumentType._member_names_],
                "access_levels": [i for i in range(0, int(max_level) + 1)],
                "user_profile": user_profile.get("data"),
                "is_admin": request.cookies.get("is_admin"),
            }
        )
