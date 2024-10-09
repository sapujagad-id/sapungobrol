from anthropic import Anthropic
from .engine import ChatEngine

class ChatAnthropic(ChatEngine):

    def __init__(self, api_key: str) -> None:
        super().__init__()
        self.client = Anthropic(api_key=api_key)

    def _get_generate_system(self) -> dict:
        return {
            "role": "system",
            "content": """
                        You are an assistant that can only provide responses based on the PROVIDED CONTEXT. 
                        DO NOT USE AN EXTERNAL/GENERAL KNOWLEDGE, only answer based on PROVIDED CONTEXT. !!!
                        """,
        }

    def _api_call(self, full_input: str):
        response = self.client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1024,
            messages=self.history,
        )
        return response.content[0].text
