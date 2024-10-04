import openai
from config import AppConfig
from abc import ABC, abstractmethod
from chat.exceptions import ChatResponseGenerationError

class Chat(ABC):
    @abstractmethod
    def generate_response(self, query: str, context: str = None) -> str:
        """Generate a response based on the query and optional context."""
        pass

class ChatOpenAI(Chat):
    
    def __init__(self):
        config = AppConfig()
        openai.api_key = config.openai_api_key
        self.history = []

    def generate_response(self, query, context=None):
        if not query:
            return ""  
        
        if context:
            full_input = f"Given a context: {context}\n Given a query: {query}\n Please answer query based on the given context"
        else:
            full_input = query
        
        self.history.append({"role": "user", "content": full_input})
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=self.history,
            )
            
            assistant_response = response['choices'][0]['message']['content']
            
            self.history.append({"role": "assistant", "content": assistant_response})
            
            return assistant_response
        except Exception as e:
            raise ChatResponseGenerationError(f"Error generating response: {str(e)}")
            
    def reset_history(self):
        self.history = []
