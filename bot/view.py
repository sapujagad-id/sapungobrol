from abc import ABC, abstractmethod

from fastapi import Request
from fastapi.templating import Jinja2Templates

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
    
# note: authentication not impl yet
class BotViewV1(BotView):    
    def __init__(self, controller: BotController, service: BotService) -> None:
        super().__init__()
        self.templates = Jinja2Templates(directory="bot/templates")
        self.controller = controller
        self.service = service
    
    def show_list_chatbots(self, request: Request):
        bots = self.controller.fetch_chatbots()
        
        return self.templates.TemplateResponse(
            request=request, 
            name="list.html", 
            context={"bots": bots},
        )
        
    def show_edit_chatbot(self, id: str, request:Request):
        bot = self.service.get_chatbot_by_id(id)
        return self.templates.TemplateResponse(
            request=request,
            name="edit-chatbot.html",
            context =   {   
                            "model_engines": [e.value for e in ModelEngine],
                            "bot":bot,
                            "message_adapters": [e.value for e in MessageAdapter]
                        }
        )

    def show_create_chatbots(self, request: Request):
        return self.templates.TemplateResponse(
            request=request,
            name="create-chatbot.html",
            context =   {   
                            "model_engines": [e.value for e in ModelEngine],
                            "message_adapters": [e.value for e in MessageAdapter]
                        }
        )

    
    