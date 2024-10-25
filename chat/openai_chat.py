import openai
from .engine import ChatEngine

class ChatOpenAI(ChatEngine):

    def _get_generate_system(self) -> dict:
        return {
            "role": "system",
            "content": """
                        You are an assistant that can only provide responses based on the PROVIDED CONTEXT. 
                        DO NOT USE AN EXTERNAL/GENERAL KNOWLEDGE, only answer based on PROVIDED CONTEXT. !!!
                        """,
        }

    def _api_call(self, full_input: str):
        response = openai.chat.completions.create(
            model="gpt-4o-mini",
            messages=self.history,
        )
        return response.choices[0].message.content
