import openai

from .engine import ChatEngine
from chat.exceptions import ChatResponseGenerationError


class ChatOpenAI(ChatEngine):

    def __init__(self):
        self.history = [self._get_generate_system()]

    def _get_generate_system(self) -> dict:

        return {
            "role": "system",
            "content": """
                        You are an assistant that can only provide responses based on the PROVIDED CONTEXT. 
                        DO NOT USE AN EXTERNAL/GENERAL KNOWLEDGE, only answer based on PROVIDED CONTEXT. !!!
                        """,
        }

    def generate_response(self, query: str, context: str = None) -> str:
        if not query:
            return ""

        if context:
            full_input = f"Given a context: {context}\n Given a query: {query}\n Please answer query based on the given context."
        else:
            full_input = query

        self.history.append({"role": "user", "content": full_input})

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=self.history,
            )

            assistant_response = response["choices"][0]["message"]["content"]

            self.history.append({"role": "assistant", "content": assistant_response})

            return assistant_response
        except Exception as e:
            raise ChatResponseGenerationError(f"Error generating response: {str(e)}")

    def reset_history(self):
        """Reset the chat history."""
        self.history = [self._get_generate_system()]
