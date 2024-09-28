from abc import ABC, abstractmethod

from fastapi import Request
from fastapi.templating import Jinja2Templates

from bot.controller import BotController


class BotView(ABC):
    @abstractmethod
    def show_list_chatbots(self):
        pass
      
    @abstractmethod
    def show_create_chatbots(self):
        pass
    
    @abstractmethod
    def show_edit_chatbot(self, id: str):
        pass
    
# note: authentication not impl yet
class BotViewV1(BotView):    
    def __init__(self, controller: BotController) -> None:
        super().__init__()
        self.templates = Jinja2Templates(directory="bot/templates")
        self.controller = controller
    
    def show_list_chatbots(self, request: Request):
        bots = self.controller.fetch_chatbots()
        
        return self.templates.TemplateResponse(
            request=request, 
            name="list.html", 
            context={"bots": bots},
        )
        
    def show_edit_chatbot(self, id: str):
        # TODO
        raise NotImplementedError

    def show_create_chatbots(self):
        # TODO
        raise NotImplementedError

    
    