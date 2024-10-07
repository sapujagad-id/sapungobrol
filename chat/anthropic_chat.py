from anthropic import Anthropic
from .engine import ChatEngine
from chat.exceptions import ChatResponseGenerationError


class ChatAnthropic(ChatEngine):

    def __init__(self):
        self.client = Anthropic(api_key="aaaaa")
        self.history = []

    def generate_response(self, query: str, context: str = None) -> str:
        if not query:
            return ""

        if context:
            full_input = f"Given a context: {context}\n Given a query: {query}\n Please answer query based on the given context."
        else:
            full_input = query

        self.history.append({"role": "user", "content": full_input})
        
        try:
            response = Anthropic().messages.create(
                model="claude-3-5-sonnet-20240620",
                max_tokens = 1024,
                messages=self.history,
                system="""
                        You are an assistant that can only provide responses based on the PROVIDED CONTEXT. 
                        DO NOT USE AN EXTERNAL/GENERAL KNOWLEDGE, only answer based on PROVIDED CONTEXT. !!!
                        """
            )
            
            assistant_response = response.content[0].text
            
            self.history.append({"role": "assistant", "content": full_input})
            
            return assistant_response
        except Exception as e:
            raise ChatResponseGenerationError(f"Error generating response: {str(e)}")
    
    def reset_history(self):
        """Reset the chat history."""
        self.history = [self._get_generate_system()]

if __name__=="__main__":
    
    chat = ChatAnthropic()
    print(chat.generate_response("Jokowi is the president of Indonesia"))
    print(chat.generate_response("Siapa itu Jokowi?"))
