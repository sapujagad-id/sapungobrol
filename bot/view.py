from abc import ABC, abstractmethod

import jinja2
from fastapi import Request
from fastapi.exceptions import HTTPException
from fastapi.templating import Jinja2Templates
from jinja2 import Environment

from auth.controller import AuthController
from bot.controller import BotController
from bot.service import BotService
from common.shared_types import MessageAdapter

from .bot import ModelEngine


class BotView(ABC):
    @abstractmethod
    def show_list_chatbots(self, request: Request): # pragma: no cover
        pass
      
    @abstractmethod
    def show_create_chatbots(self, request:Request): # pragma: no cover
        pass
    
    @abstractmethod
    def show_edit_chatbot(self, id: str, request:Request): # pragma: no cover
        pass
    
    @abstractmethod
    def show_login(self, request: Request): # pragma: no cover
        pass
    
# note: authentication not impl yet
class BotViewV1(BotView):    
    def __init__(self, controller: BotController, service: BotService, auth_controller: AuthController) -> None:
        super().__init__()
        self.templates = Jinja2Templates(
            env=Environment(
                loader=jinja2.FileSystemLoader(['bot/templates', 'components/templates']),
                autoescape=True,
            )
        )
        self.controller = controller
        self.service = service
        self.auth_controller = auth_controller
    
    def show_list_chatbots(self, request: Request):
        bots = self.controller.fetch_chatbots()
        user_profile = self.auth_controller.user_profile_google(request)
        return self.templates.TemplateResponse(
            request=request, 
            name="list.html", 
            context={"bots": bots,
                    "is_admin": request.cookies.get("is_admin"),
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
                            "is_admin": request.cookies.get("is_admin"),
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
                "is_admin": request.cookies.get("is_admin"),
                "user_profile": user_profile.get("data"),
                "data_source":["docs1","docs2","docs3"]
            }
        )
        
    def show_dashboard(self, request: Request):
        user_profile = self.auth_controller.user_profile_google(request)
        bots = self.controller.fetch_chatbots()
        return self.templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={"bots": bots, "user_profile": user_profile.get("data")}
        )
        
    def show_dashboard_with_id(self, request: Request, bot_id: str):
        user_profile = self.auth_controller.user_profile_google(request)
        bots = self.controller.fetch_chatbots()

        # Validate if bot_id exists
        selected_bot = next((bot for bot in bots if bot.id == bot_id), None)
        if not selected_bot:
            raise HTTPException(status_code=404, detail="Bot not found")

        return self.templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "bots": bots,
                "user_profile": user_profile.get("data"),
                "selected_bot_id": bot_id,  # Pass selected bot ID to the template
            }
        )
    
    def show_login(self, request: Request):
        return self.templates.TemplateResponse(
            request=request,
            name="login.html",
            context={}
        )

    
    