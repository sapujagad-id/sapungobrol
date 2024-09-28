from openai import OpenAI
from config import AppConfig
from abc import ABC, abstractmethod

class Chat(ABC):
    @abstractmethod
    def generate_response(self, query: str, context: str = None) -> str:
        """Generate a response based on the query and optional context."""
        pass
    
class ChatOpenAI(Chat):
    
    def __init__(self):
        config = AppConfig()
        self.llm = OpenAI(api_key=config.openai_api_key) 

    def generate_response(query, context=None):
        if not query:
            return ""  
        llm = OpenAI() 
        
        if context:
            full_input = f"Given a context: {context}\n Given a query: {query}\n Please answer query based on the given context"
        else:
            full_input = query
        
        resp = llm.run(full_input)
        return resp