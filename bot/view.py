from abc import ABC, abstractmethod

from fastapi import Request
from fastapi.templating import Jinja2Templates
from jinja2 import Environment
import jinja2

from auth.controller import AuthController
from bot.service import BotService

from .bot import MessageAdapter, ModelEngine
from bot.controller import BotController


class BotView(ABC):
    @abstractmethod
    def show_list_chatbots(self, request: Request):
        pass
      
    @abstractmethod
    def show_create_chatbots(self, request:Request):
        pass
    
    @abstractmethod
    def show_edit_chatbot(self, id: str, request:Request):
        pass
    
    @abstractmethod
    def show_login(self, request: Request):
        pass
    
# note: authentication not impl yet
class BotViewV1(BotView):    
    def __init__(self, controller: BotController, service: BotService, auth_controller: AuthController, admin_emails=list[str]) -> None:
        super().__init__()
        self.templates = Jinja2Templates(
            env=Environment(
                loader=jinja2.FileSystemLoader('bot/templates'),
                autoescape=True,
            )
        )
        self.controller = controller
        self.service = service
        self.auth_controller = auth_controller
        self.admin_emails = admin_emails
    
    def show_list_chatbots(self, request: Request):
        bots = self.controller.fetch_chatbots()
        user_profile = self.auth_controller.user_profile_google(request)
        return self.templates.TemplateResponse(
            request=request, 
            name="list.html", 
            context={"bots": bots,
                    "admin_emails": self.admin_emails,
                     "user_profile": user_profile.get("data")
                     },
        )
        
    def show_edit_chatbot(self, id: str, request:Request):
        user_profile = self.auth_controller.user_profile_google(request)
        bot = self.service.get_chatbot_by_id(id)
        return self.templates.TemplateResponse(
            request=request,
            name="edit-chatbot.html",
            context =   {   
                            "model_engines": [e.value for e in ModelEngine],
                            "bot":bot,
                            "admin_emails": self.admin_emails,
                            "message_adapters": [e.value for e in MessageAdapter],
                            "user_profile": user_profile.get("data"),
                            "data_source":["docs1","docs2","docs3"]
                        }
        )

    def show_create_chatbots(self, request: Request):
        user_profile = self.auth_controller.user_profile_google(request)  # Make sure to await if this is a coroutine
        return self.templates.TemplateResponse(
            request=request,
            name="create-chatbot.html",
            context={   
                "model_engines": [e.value for e in ModelEngine],
                "message_adapters": [e.value for e in MessageAdapter],
                "admin_emails": self.admin_emails,
                "user_profile": user_profile.get("data"),
                "data_source":["docs1","docs2","docs3"]
            }
        )
    
    def show_login(self, request: Request):
        return self.templates.TemplateResponse(
            request=request,
            name="login.html",
            context={}
        )

    
    